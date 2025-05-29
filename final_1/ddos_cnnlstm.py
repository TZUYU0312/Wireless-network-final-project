import pandas as pd
import numpy as np
from joblib import dump
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import classification_report, precision_recall_curve, average_precision_score
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
from sklearn.feature_selection import SelectKBest, f_classif
import matplotlib.pyplot as plt
import seaborn as sns


from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv1D, LSTM, Dense, Dropout, MaxPooling1D, Flatten
from tensorflow.keras.layers import BatchNormalization
from tensorflow.keras.callbacks import EarlyStopping

# === 1. 載入資料並預處理 ===
#Timestamp -> bidirectional_first_seen_ms
df = pd.read_csv("interface_flows.csv", parse_dates=["bidirectional_first_seen_ms"])
#df = pd.read_csv("interface_flows_3.csv", parse_dates=["bidirectional_first_seen_ms"])
#df[['Source', 'Destination', *_]] = df['Flow ID'].str.split('-', expand=True)
##flow_split = df['Flow ID'].str.split('-', expand=True)
##df['Source'] = flow_split[0]
##df['Destination'] = flow_split[1]
df = df.sort_values("bidirectional_first_seen_ms")
##df[['SourceIP_1', 'SourceIP_2', 'SourceIP_3', 'SourceIP_4']] = df['Source'].str.split('.', expand=True)
##df[['DestinationIP_1', 'DestinationIP_2', 'DestinationIP_3', 'DestinationIP_4']] = df['Destination'].str.split('.', expand=True)

##df = df.drop(columns=["Flow ID", "Timestamp", "Source", "Destination", "Source Port", "Dest Port", "Other"], errors='ignore')

# Label encoding
le = LabelEncoder()
df['Label_encoded'] = le.fit_transform(df['Label'])

X = df.drop(columns=["Label", "Label_encoded"])
X = X.apply(pd.to_numeric, errors='coerce').fillna(0)
y = df['Label_encoded'].values

# === 2. 標準化與序列化（以時間為序列）===
scaler = StandardScaler()
# 特徵數可以試 50（論文提到是最佳）
k_best = SelectKBest(score_func=f_classif, k=50)
X_selected = k_best.fit_transform(X, y)
X_scaled = scaler.fit_transform(X_selected)

def create_sequences(X, y, window_size=10):
    X_seq, y_seq = [], []
    for i in range(len(X) - window_size):
        X_seq.append(X[i:i+window_size])
        y_seq.append(y[i+window_size])  # 預測最後一筆
    return np.array(X_seq), np.array(y_seq)

X_seq, y_seq = create_sequences(X_scaled, y, window_size=10)

# 分割訓練與測試
split = int(0.6 * len(X_seq))
X_train, X_test = X_seq[:split], X_seq[split:]
y_train, y_test = y_seq[:split], y_seq[split:]

# === 3. CNN-LSTM 模型建立 ===
model = Sequential()
model.add(Conv1D(filters=16, kernel_size=1, activation='relu',padding='same', input_shape=(X_train.shape[1], X_train.shape[2])))
model.add(MaxPooling1D(pool_size=2))
model.add(BatchNormalization())
#model.add(Dropout(0.2))
model.add(LSTM(16, return_sequences = True))  # 第一層 LSTM return_sequences=True 才能接第二層
#model.add(Dropout(0.2))

# 第二層
model.add(Conv1D(filters=32, kernel_size=3, activation='relu',padding='same'))
model.add(MaxPooling1D(pool_size=2))
model.add(BatchNormalization())
#model.add(Dropout(0.2))
model.add(LSTM(32, return_sequences = True))  # 最後一層 LSTM 不需 return_sequences

# 第三層
model.add(Conv1D(filters=64, kernel_size=5, activation='relu',padding='same'))
model.add(MaxPooling1D(pool_size=2))
model.add(BatchNormalization())
model.add(Dropout(0.2))
model.add(LSTM(64))  # 最後一層 LSTM 不需 return_sequences
model.add(Dense(64, activation='relu'))
model.add(Dense(1, activation='sigmoid'))  # 二分類

model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])
model.summary()


# === 4. 訓練 ===
history = model.fit(X_train, y_train, epochs=10, batch_size=128, validation_split=0.1,
          callbacks=[EarlyStopping(monitor='val_loss', patience=2)], verbose=1)

# === 5. 評估 ===
y_prob = model.predict(X_test).ravel()
y_pred = (y_prob > 0.5).astype(int)

#print("\n=== Classification Report (CNN-LSTM) ===")
#print(classification_report(y_test, y_pred, target_names=le.classes_))
target_names = [str(c) for c in le.classes_]
print(classification_report(y_test, y_pred, target_names=target_names))
# PR Curve
precision, recall, _ = precision_recall_curve(y_test, y_prob)
ap = average_precision_score(y_test, y_prob)

plt.figure(figsize=(8,6))
plt.plot(recall, precision, label=f'AP = {ap:.2f}')
plt.xlabel("Recall")
plt.ylabel("Precision")
plt.title("PR Curve (CNN-LSTM)")
plt.grid()
plt.legend()
plt.show()


#confusion matrix
cm = confusion_matrix(y_test, y_pred)
disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=le.classes_)
disp.plot(cmap='Blues')
plt.title("Confusion Matrix (CNN-LSTM)")
plt.show()

# Loss 圖
plt.figure(figsize=(10, 4))
plt.subplot(1, 2, 1)
plt.plot(history.history['loss'], label='Train Loss', marker='o')
plt.plot(history.history['val_loss'], label='Val Loss', marker='o')
plt.title('Model Loss Over Epochs')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.grid(True)
plt.legend()

# Accuracy 圖（如果模型有 accuracy）
if 'accuracy' in history.history:
    plt.subplot(1, 2, 2)
    plt.plot(history.history['accuracy'], label='Train Acc', marker='o')
    plt.plot(history.history['val_accuracy'], label='Val Acc', marker='o')
    plt.title('Model Accuracy Over Epochs')
    plt.xlabel('Epoch')
    plt.ylabel('Accuracy')
    plt.grid(True)
    plt.legend()

plt.tight_layout()
plt.show()


# === 6. 儲存模型與前處理器 ===


# 儲存模型（HDF5 格式）
model.save("cnn_lstm_model.h5")

# 儲存標準化器與特徵選擇器
dump(scaler, "scaler_cnn_lstm.pkl")
dump(k_best, "kbest_cnn_lstm.pkl")

print("✅ 模型與前處理器儲存成功！")
