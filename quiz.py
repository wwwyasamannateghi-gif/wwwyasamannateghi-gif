import json
import streamlit as st

ALLOWED_TOPIC_RULE="""The quiz topic must be related to Computer Science, Computers, Artificial Intelligence, Machine Learning, Python, Programming, Algorithms, Hardware, Software, Internet, Networks, Data, Information, or closely related computer-education topics."""

def generate_quiz(client,topic):
    prompt=f'''Create a 5-question educational multiple-choice quiz about:\n\n{topic}\n\n{ALLOWED_TOPIC_RULE}\n\nEach question must have exactly 4 options. Only one option is correct. Return ONLY valid JSON, no Markdown, using this structure:\n[{{"question":"سؤال","options":["گزینه ۱","گزینه ۲","گزینه ۳","گزینه ۴"],"answer":0,"explanation":"توضیح آموزشی"}}]\nanswer must be 0,1,2,or 3. Questions should test understanding and be suitable for students. Return ONLY the JSON array.'''
    try:
        response=client.chat.send(model="openrouter/free",messages=[{"role":"system","content":"You are an educational quiz generator. Return only valid JSON. Do not return Markdown."},{"role":"user","content":prompt}])
        text=response.choices[0].message.content.strip().replace("```json","").replace("```","").strip()
        questions=json.loads(text)
        if not isinstance(questions,list) or not questions: raise ValueError("خروجی آزمون معتبر نیست.")
        validated=[]
        for item in questions:
            if not isinstance(item,dict) or not {"question","options","answer","explanation"}.issubset(item): raise ValueError("ساختار یکی از سؤال‌ها معتبر نیست.")
            if not isinstance(item["options"],list) or len(item["options"])!=4: raise ValueError("هر سؤال باید دقیقاً ۴ گزینه داشته باشد.")
            if not isinstance(item["answer"],int) or item["answer"] not in range(4): raise ValueError("شماره پاسخ صحیح معتبر نیست.")
            validated.append({"question":str(item["question"]),"options":[str(x) for x in item["options"]],"answer":item["answer"],"explanation":str(item["explanation"])})
        return validated
    except Exception as e:
        st.error("❌ ساخت آزمون با خطا مواجه شد."); st.code(str(e)); return None

def reset_quiz_state():
    for key in ["quiz_topic","quiz_questions","quiz_index","quiz_score","quiz_answered","quiz_finished","answer_correct","selected_answer","quiz_requested_topic","quiz_started"]:
        st.session_state.pop(key,None)

def start_quiz(client,topic):
    if st.session_state.get("quiz_topic")!=topic:
        st.session_state.quiz_topic=topic; st.session_state.quiz_questions=None; st.session_state.quiz_index=0; st.session_state.quiz_score=0; st.session_state.quiz_answered=False; st.session_state.quiz_finished=False; st.session_state.answer_correct=False; st.session_state.selected_answer=None
    if st.session_state.quiz_questions is None:
        with st.spinner("🤖 در حال ساخت آزمون..."): questions=generate_quiz(client,topic)
        if not questions:return
        st.session_state.quiz_questions=questions
    questions=st.session_state.quiz_questions
    if st.session_state.quiz_finished:
        total=len(questions); score=st.session_state.quiz_score; percentage=round(score/total*100) if total else 0
        st.markdown("---"); st.markdown("## 🎉 آزمون تمام شد!"); st.metric("درصد نهایی",f"{percentage}%")
        c1,c2=st.columns(2)
        with c1: st.success(f"✅ پاسخ صحیح: {score}")
        with c2: st.error(f"❌ پاسخ غلط: {total-score}")
        if percentage>=80: st.success("🌟 عالی بود! تسلط خیلی خوبی روی این مبحث داری.")
        elif percentage>=50: st.info("👍 خوب بود! با کمی تمرین بیشتر بهتر هم می‌شوی.")
        else: st.warning("📚 بهتر است این مبحث را دوباره مرور کنی و دوباره امتحان بدهی.")
        if st.button("🔄 آزمون جدید",key="new_quiz_button"): reset_quiz_state(); st.rerun()
        return
    index=st.session_state.quiz_index; question=questions[index]
    st.markdown("---"); st.markdown(f"### 📝 سؤال {index+1} از {len(questions)}"); st.progress((index+1)/len(questions)); st.markdown(f"## {question['question']}")
    if not st.session_state.quiz_answered:
        selected=st.radio("گزینه خود را انتخاب کنید:",question["options"],key=f"quiz_option_{index}")
        if st.button("✅ ثبت پاسخ",key=f"submit_answer_{index}"):
            selected_index=question["options"].index(selected); st.session_state.selected_answer=selected_index; st.session_state.answer_correct=selected_index==question["answer"]; st.session_state.quiz_answered=True
            if st.session_state.answer_correct: st.session_state.quiz_score+=1
            st.rerun()
    else:
        correct_index=question["answer"]
        if st.session_state.answer_correct: st.success("🎉 پاسخ شما صحیح است!")
        else: st.error("❌ پاسخ شما اشتباه است."); st.info("پاسخ صحیح: "+question["options"][correct_index])
        st.markdown("### 📚 توضیح آموزشی"); st.write(question["explanation"])
        if index < len(questions) - 1:
            if st.button("➡️ سؤال بعدی", key=f"next_question_{index}"):
                st.session_state.quiz_index += 1
                st.session_state.quiz_answered = False
                st.session_state.selected_answer = None
                st.rerun()
        else:
            if st.button("🏁 مشاهده نتیجه نهایی", key="finish_quiz_button"):
                st.session_state.quiz_finished = True
                st.rerun()
