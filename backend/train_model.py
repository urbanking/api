import pandas as pd
import torch
from transformers import BertTokenizer, BertForSequenceClassification, Trainer, TrainingArguments
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from database import get_connection

# 데이터 로드
def load_data_from_db():
    conn = get_connection()
    try:
        query = "SELECT content, 광고 FROM cr_data"
        data = pd.read_sql(query, conn)
    finally:
        conn.close()
    return data

data = load_data_from_db()

# 데이터 전처리
data['label'] = data['광고'].apply(lambda x: 1 if x == 'O' else 0)
train_texts, val_texts, train_labels, val_labels = train_test_split(data['content'], data['label'], test_size=0.3)

# 토크나이저 로드
tokenizer = BertTokenizer.from_pretrained('bert-base-multilingual-cased')

# 토큰화
train_encodings = tokenizer(list(train_texts), truncation=True, padding=True, max_length=512)
val_encodings = tokenizer(list(val_texts), truncation=True, padding=True, max_length=512)

# 토크나이저 결과 출력
print("Train Encodings Sample:", train_encodings['input_ids'][:1])
print("Validation Encodings Sample:", val_encodings['input_ids'][:1])

# 데이터셋 클래스 정의
class AdDataset(torch.utils.data.Dataset):
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels

    def __getitem__(self, idx):
        item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
        item['labels'] = torch.tensor(self.labels[idx])
        return item

    def __len__(self):
        return len(self.labels)

# 데이터셋 생성
train_dataset = AdDataset(train_encodings, train_labels)
val_dataset = AdDataset(val_encodings, val_labels)

# 모델 로드
model = BertForSequenceClassification.from_pretrained('bert-base-multilingual-cased', num_labels=2)

# 평가 메트릭 정의
def compute_metrics(pred):
    labels = pred.label_ids
    preds = pred.predictions.argmax(-1)
    precision, recall, f1, _ = precision_recall_fscore_support(labels, preds, average='binary')
    acc = accuracy_score(labels, preds)
    return {
        'accuracy': acc,
        'f1': f1,
        'precision': precision,
        'recall': recall
    }

# 트레이너 설정
training_args = TrainingArguments(
    output_dir='./results',
    num_train_epochs=3,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    warmup_steps=500,
    weight_decay=0.01,
    logging_steps=10,
    eval_strategy="epoch",  # 여기 콤마를 추가합니다.
    # logging_dir을 명시적으로 설정하거나 필요한 경우 제거합니다.
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
    compute_metrics=compute_metrics
)

# 모델 학습
trainer.train()

# 모델 저장
model.save_pretrained('./ad_model')
tokenizer.save_pretrained('./ad_model')