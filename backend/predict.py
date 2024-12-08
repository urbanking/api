import torch
import pandas as pd
from transformers import BertTokenizer, BertForSequenceClassification
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from sklearn.model_selection import train_test_split
from database import get_connection

# 모델 로드
model = BertForSequenceClassification.from_pretrained('./ad_model')
tokenizer = BertTokenizer.from_pretrained('./ad_model')
model.eval()  # 평가 모드로 전환

def predict_ad(text: str) -> str:
    inputs = tokenizer(text, return_tensors='pt', truncation=True, padding=True, max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
    probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
    return '1' if probs[0][1] > 0.5 else '0'

def load_test_data_from_db():
    conn = get_connection()
    try:
        query = "SELECT content, 광고 FROM cr_data"
        data = pd.read_sql(query, conn)
    finally:
        conn.close()
    return data

# 테스트 데이터 로드
data = load_test_data_from_db()
_, test_data = train_test_split(data, test_size=0.3)
test_texts = test_data['content']
test_labels = test_data['광고'].apply(lambda x: 1 if x == 'O' else 0)

# 예측 및 평가
predictions = [predict_ad(text) for text in test_texts]
pred_labels = [1 if pred == '1' else 0 for pred in predictions]

precision, recall, f1, _ = precision_recall_fscore_support(test_labels, pred_labels, average='binary')
acc = accuracy_score(test_labels, pred_labels)

print(f"Accuracy: {acc}")
print(f"Precision: {precision}")
print(f"Recall: {recall}")
print(f"F1 Score: {f1}")