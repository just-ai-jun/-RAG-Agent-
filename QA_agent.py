from openai import OpenAI
from dotenv import load_dotenv
import os
import jieba

load_dotenv()
API_KEY = os.getenv("API_KEY")
MODEL_ENDPOINT = "ep-20260509214534-r7x5v"
client = OpenAI(
    api_key=API_KEY,
    base_url="https://ark.cn-beijing.volces.com/api/v3"
)


def search_knowledge(question, knowledge_entries, top_k=3):
    if not knowledge_entries:
        return ""
    words = jieba.lcut(question)
    keywords = [w for w in words if len(w) > 1]
    scored = []
    for entry in knowledge_entries:
        score = sum(1 for kw in keywords if kw in entry)
        if score > 0:
            scored.append((score, entry))
    scored.sort(reverse=True, key=lambda x: x[0])
    top_entries = [entry for _, entry in scored[:top_k]]
    return "\n\n".join(top_entries)


def load_knowledge_base():
    try:
        with open("yuanshen_knowledge.txt", "r", encoding="utf-8") as f:
            raw = f.read()
        entries = [para.strip() for para in raw.split("\n\n") if para.strip()]
        print(f"√ 原神知识库加载成功！共 {len(entries)} 条知识")
        return entries
    except FileNotFoundError:
        print("❌ 错误：找不到yuanshen_knowledge.txt文件！")
        print("请确保这个文件和main.py在同一个文件夹里，文件名完全正确")
        return []


def build_prompt(user_question, knowledge):
    prompt = f"""必须严格遵守：
回答只能来自【原神知识库】中的内容
知识库中没有明确提到就说：抱歉，这个问题我暂时还不知道，请关注原神官方公告
非原神问题就说：抱歉，我只回答原神游戏相关的问题
问题不明确就礼貌请他说清楚一点
你是原神官方专属AI客服派蒙，活泼可爱，说话元气满满，简洁亲切，口语化回答。
【强制格式】回答**只能一行纯文字**，禁止任何换行、空格、**用户问什么答什么，不要多余内容**！
【强制要求】**不要回溯历史**
【原神知识库】
{knowledge}
【玩家的问题】
{user_question}
【你的回答】
"""
    return prompt


def get_ai_answer(user_question, knowledge):
    try:
        response = client.chat.completions.create(
            model=MODEL_ENDPOINT,
            messages=[{"role": "user", "content": build_prompt(user_question, knowledge)}],
            temperature=0.1,
            max_tokens=150,
            stop=["\n"],
        )
        print(f'''本次消耗tokens：输入{response.usage.prompt_tokens}个，输出{response.usage.completion_tokens}个,总计{response.usage.total_tokens}个''')
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"❌ 调用API出错：{e}")
        return "抱歉，我现在有点忙，请稍后再试哦"


def chat_interface():
    print("=" * 50)
    print("        原神专属AI问答助手（带RAG）")
    print("=" * 50)
    knowledge = load_knowledge_base()
    if not knowledge:
        return
    print("\n💡 你可以问我任何原神5.0版本的问题")
    print("💡 输入「退出」结束聊天")
    print("-" * 50)
    all_chat_history = []
    while True:
        user_input = input("\n你的问题：")
        if user_input.strip() == "退出":
            print("\n感谢使用，再见！")
            break
        all_chat_history.append({"role": "user", "content": user_input})
        current_question = user_input
        if len(all_chat_history) >= 2:
            last_user = all_chat_history[-2]['content']
            last_answer = all_chat_history[-1]['content']
            current_question = f"上一轮玩家问：{last_user} 派蒙回答：{last_answer}，当前玩家问：{user_input}"
        retrieved_knowledge = search_knowledge(user_input, knowledge)
        answer = get_ai_answer(current_question, retrieved_knowledge)
        all_chat_history.append({"role": "assistant", "content": answer})
        print(f"派蒙：{answer}")


if __name__ == "__main__":
    chat_interface()