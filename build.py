from apikey import api
from groq import Groq
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS


with open("dataset.txt", "r", encoding="utf-8") as f:
    data = " ".join([line.strip() for line in f])

splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
chunks = splitter.create_documents([data])

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
vector_store = FAISS.from_documents(chunks, embeddings)

retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 12})

client = Groq(api_key=api)


def get_answer_from_context(question: str, context: str) -> str:
    prompt = f"""Câu hỏi: {question}
                 Ngữ cảnh: {context}
                 Trả lời:"""

    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[
            {"role": "system", "content": """Bạn là một trợ lý AI thông minh và thân thiện.
            Hãy trả lời một cách tự nhiên và dễ hiểu.
            Chỉ trả lời dựa trên thông tin được cung cấp trong ngữ cảnh.
            Nếu thông tin không đủ hoặc không chắc chắn, hãy thành thật nói rằng bạn không có đủ thông tin.
            Câu trả lời phải luôn bằng tiếng Việt.
            Khi trích dẫn, hãy đặt trong dấu ngoặc kép và chỉ rõ nguồn.
            Nếu có thể, hãy tổ chức câu trả lời theo từng ý để dễ đọc."""},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=8192,
        top_p=1,
        stream=False
    )
    return response.choices[0].message.content.strip()


question = "Shin là ai? Cho tôi biết về thông tin của Shin."
retrieved_docs = retriever.invoke(question)

context_text = "\n\n".join(doc.page_content for doc in retrieved_docs)


def format_response(answer: str) -> str:
    separator = "-" * 50
    return f"""
{separator}
Câu hỏi: {question}

Trả lời:
{answer}
{separator}
"""


answer = get_answer_from_context(question, context_text)
formatted_answer = format_response(answer)
print(formatted_answer)
