import streamlit as st
import anthropic
import os
import json
import random

# Page configuration
st.set_page_config(
    page_title="SciBot - AI Science Tutor",
    page_icon="🤖",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 0;
    }
    .sub-header {
        text-align: center;
        color: #666;
        margin-top: 0;
    }
    .stButton>button {
        width: 100%;
    }
    .quiz-card {
        background-color: #f0f8ff;
        padding: 20px;
        border-radius: 10px;
        border: 2px solid #1E88E5;
        margin: 10px 0;
    }
    .flashcard {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 30px;
        border-radius: 15px;
        text-align: center;
        min-height: 200px;
        cursor: pointer;
        margin: 20px 0;
    }
    .correct-answer {
        background-color: #d4edda;
        border: 2px solid #28a745;
        padding: 10px;
        border-radius: 5px;
    }
    .wrong-answer {
        background-color: #f8d7da;
        border: 2px solid #dc3545;
        padding: 10px;
        border-radius: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# Title and description
st.markdown('<h1 class="main-header">🤖 SciBot - Your AI Science Tutor</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Learn science with quizzes, flashcards, and smart AI help!</p>', unsafe_allow_html=True)

# Sidebar for settings and modes
with st.sidebar:
    st.header("⚙️ Settings")
    
    # Mode selection
    mode = st.selectbox(
        "Choose Mode:",
        ["💬 Chat with SciBot", "📝 Generate Quiz", "🎴 Flashcards", "📊 My Progress"]
    )
    
    st.markdown("---")
    
    # Grade level selection (replaces difficulty)
    grade_level = st.selectbox(
        "Select Your Grade Level:",
        [
            "Not Sure / Basic",
            "Kindergarten - 2nd Grade",
            "3rd - 5th Grade", 
            "6th - 8th Grade (Middle School)",
            "9th - 10th Grade (High School)",
            "11th - 12th Grade (Advanced)"
        ],
        index=3  # Default to 6th-8th grade
    )
    
    # Map grade level to difficulty description for AI
    grade_mapping = {
        "Not Sure / Basic": {
            "level": "Basic",
            "description": "Very simple explanations using everyday language. Like explaining to someone learning science for the first time.",
            "vocab": "Use only basic vocabulary. Avoid technical terms unless you explain them in very simple words."
        },
        "Kindergarten - 2nd Grade": {
            "level": "Kindergarten - 2nd Grade",
            "description": "Very simple concepts with fun examples. Use short sentences and relate to things kids see every day.",
            "vocab": "Use only simple words a young child would know. Compare to toys, animals, playground, food."
        },
        "3rd - 5th Grade": {
            "level": "Elementary (3rd-5th Grade)",
            "description": "Clear explanations with relatable examples. Introduce basic scientific terms but explain them.",
            "vocab": "Use elementary-level vocabulary. You can use some science words but always explain what they mean."
        },
        "6th - 8th Grade (Middle School)": {
            "level": "Middle School (6th-8th Grade)",
            "description": "More detailed explanations with scientific vocabulary. Students can handle more complex concepts.",
            "vocab": "Use middle school level vocabulary and standard scientific terms. Give examples from everyday life."
        },
        "9th - 10th Grade (High School)": {
            "level": "High School (9th-10th Grade)",
            "description": "Detailed scientific explanations with proper terminology. Include more complex concepts and relationships.",
            "vocab": "Use high school level vocabulary. Include chemical formulas, equations, and scientific processes."
        },
        "11th - 12th Grade (Advanced)": {
            "level": "Advanced High School (11th-12th Grade)",
            "description": "In-depth scientific explanations. Can include advanced concepts, formulas, and theoretical understanding.",
            "vocab": "Use advanced vocabulary. Include complex theories, mathematical relationships, and detailed mechanisms."
        }
    }
    
    current_grade = grade_mapping[grade_level]
    
    # Topic selection
    topic = st.selectbox(
        "Choose a Science Topic:",
        ["General Science", "Biology", "Chemistry", "Physics", "Earth Science", "Space & Astronomy", "Human Body"]
    )
    
    # Explanation style
    style = st.radio(
        "Explanation Style:",
        ["Normal", "Extra Simple", "Very Detailed"]
    )
    
    st.markdown("---")
    st.markdown("### 🎯 About SciBot")
    st.info("SciBot is your friendly AI science tutor! Ask questions, take quizzes, or study with flashcards!")
    
    # Display current settings
    st.markdown("### 📚 Current Settings")
    st.text(f"Grade: {current_grade['level']}")
    st.text(f"Topic: {topic}")
    st.text(f"Style: {style}")
    
    # Stats
    if "questions_answered" not in st.session_state:
        st.session_state.questions_answered = 0
    if "quizzes_taken" not in st.session_state:
        st.session_state.quizzes_taken = 0
    if "quiz_score" not in st.session_state:
        st.session_state.quiz_score = 0
    
    st.markdown("---")
    st.markdown("### 📈 Your Stats")
    st.metric("Questions Asked", st.session_state.questions_answered)
    st.metric("Quizzes Taken", st.session_state.quizzes_taken)
    if st.session_state.quizzes_taken > 0:
        avg_score = (st.session_state.quiz_score / st.session_state.quizzes_taken)
        st.metric("Average Quiz Score", f"{avg_score:.0f}%")

# API Key setup
api_key = os.environ.get("ANTHROPIC_API_KEY", "")

if not api_key:
    api_key = st.text_input("🔑 Enter Your Anthropic API Key:", type="password", help="Get your free API key from https://console.anthropic.com/")
    if api_key:
        os.environ["ANTHROPIC_API_KEY"] = api_key

# Initialize session states
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_quiz" not in st.session_state:
    st.session_state.current_quiz = None
if "quiz_answers" not in st.session_state:
    st.session_state.quiz_answers = {}
if "flashcards" not in st.session_state:
    st.session_state.flashcards = []
if "current_flashcard" not in st.session_state:
    st.session_state.current_flashcard = 0
if "show_flashcard_answer" not in st.session_state:
    st.session_state.show_flashcard_answer = False

# Function to call Claude AI
def call_scibot(prompt, system_prompt):
    if not api_key:
        return "Please enter your API key first!"
    
    try:
        client = anthropic.Anthropic(api_key=api_key)
        
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return message.content[0].text
    except Exception as e:
        return f"Oops! SciBot encountered an error: {str(e)}"

# MODE 1: CHAT WITH SCIBOT
if mode == "💬 Chat with SciBot":
    st.markdown("### 💬 Ask SciBot Anything!")
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask me a science question..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.questions_answered += 1
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate SciBot's response
        with st.chat_message("assistant", avatar="🤖"):
            # Adjust system prompt based on style
            style_instruction = ""
            if style == "Extra Simple":
                style_instruction = "Use VERY simple language. Explain like you're talking to someone younger. Use fun analogies and examples."
            elif style == "Very Detailed":
                style_instruction = "Provide detailed, comprehensive explanations with multiple examples and deeper context."
            else:
                style_instruction = "Use clear, conversational language appropriate for the grade level."
            
            system_prompt = f"""You are SciBot, a friendly and enthusiastic AI science tutor! 

Your personality:
- Friendly and encouraging
- Makes science fun and exciting
- Uses examples students can relate to
- Celebrates curiosity and learning
- Sometimes uses emojis to be friendly

CRITICAL - Grade Level Adjustment:
Student Grade Level: {current_grade['level']}
{current_grade['description']}
{current_grade['vocab']}

Topic focus: {topic}
Explanation style: {style}
{style_instruction}

Instructions:
- Always start responses with enthusiasm (like "Great question!" or "Ooh, that's interesting!")
- Explain concepts clearly and accurately AT THE APPROPRIATE GRADE LEVEL
- Adjust vocabulary and complexity to match {current_grade['level']}
- Use real-world examples that students at this grade would understand
- For younger grades: Use more analogies, simpler words, shorter explanations
- For older grades: Can use more technical terms, complex concepts, detailed explanations
- Encourage curiosity and ask if they want to know more
- If a question is not about science, politely redirect: "I'm SciBot, your science tutor! I'm best at science questions. Want to ask about {topic}?"
- Keep answers engaging but concise (2-4 paragraphs unless more detail is requested)
- Sign off as "- SciBot 🤖" occasionally
"""
            
            response = call_scibot(prompt, system_prompt)
            st.markdown(response)
            
            st.session_state.messages.append({"role": "assistant", "content": response})
    
    # Clear chat button
    if st.session_state.messages:
        if st.button("🗑️ Clear Chat History"):
            st.session_state.messages = []
            st.rerun()
    
    # Show example questions if no messages
    if not st.session_state.messages:
        st.markdown("---")
        st.markdown("### 💡 Try asking SciBot:")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**🧬 Biology**")
            if st.button("How do plants breathe?"):
                st.session_state.messages.append({"role": "user", "content": "How do plants breathe?"})
                st.rerun()
            if st.button("Why do we need sleep?"):
                st.session_state.messages.append({"role": "user", "content": "Why do we need sleep?"})
                st.rerun()
        
        with col2:
            st.markdown("**⚗️ Chemistry**")
            if st.button("What makes fireworks colorful?"):
                st.session_state.messages.append({"role": "user", "content": "What makes fireworks colorful?"})
                st.rerun()
            if st.button("Why does ice float?"):
                st.session_state.messages.append({"role": "user", "content": "Why does ice float on water?"})
                st.rerun()
        
        with col3:
            st.markdown("**🌍 Physics**")
            if st.button("How do planes fly?"):
                st.session_state.messages.append({"role": "user", "content": "How do airplanes fly?"})
                st.rerun()
            if st.button("What is electricity?"):
                st.session_state.messages.append({"role": "user", "content": "What is electricity?"})
                st.rerun()

# MODE 2: GENERATE QUIZ
elif mode == "📝 Generate Quiz":
    st.markdown("### 📝 Test Your Knowledge!")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        quiz_topic = st.text_input("What topic do you want to be quizzed on?", 
                                   placeholder=f"e.g., Photosynthesis, States of Matter, Solar System...")
    
    with col2:
        num_questions = st.slider("Number of Questions:", 3, 10, 5)
    
    if st.button("🎲 Generate Quiz", type="primary"):
        if not api_key:
            st.warning("Please enter your API key first!")
        elif not quiz_topic:
            st.warning("Please enter a topic for your quiz!")
        else:
            with st.spinner("SciBot is creating your quiz..."):
                system_prompt = f"""You are SciBot, creating a science quiz.

CRITICAL - Grade Level Adjustment:
Student Grade Level: {current_grade['level']}
{current_grade['description']}
{current_grade['vocab']}

Create a quiz with EXACTLY {num_questions} multiple choice questions about: {quiz_topic}

IMPORTANT: Adjust question difficulty and vocabulary to match {current_grade['level']}:
- For younger grades: Use simpler concepts, everyday examples, basic vocabulary
- For middle grades: Standard concepts with appropriate scientific terms
- For older grades: More complex concepts, advanced vocabulary, detailed scenarios

CRITICAL: Return ONLY valid JSON, nothing else. No markdown, no backticks, no explanations.

Format:
{{
  "title": "Quiz Title (grade-appropriate)",
  "questions": [
    {{
      "question": "Question text appropriate for {current_grade['level']}?",
      "options": ["A) option1", "B) option2", "C) option3", "D) option4"],
      "correct": "A",
      "explanation": "Why this is correct (explained at {current_grade['level']} level)"
    }}
  ]
}}

Make questions engaging and educational at the appropriate level!"""
                
                prompt = f"Create a {num_questions}-question quiz about {quiz_topic} for {current_grade['level']} level"
                
                response = call_scibot(prompt, system_prompt)
                
                try:
                    # Clean up response
                    response = response.strip()
                    if response.startswith("```"):
                        response = response.split("```")[1]
                        if response.startswith("json"):
                            response = response[4:]
                    response = response.strip()
                    
                    quiz_data = json.loads(response)
                    st.session_state.current_quiz = quiz_data
                    st.session_state.quiz_answers = {}
                    st.success("✅ Quiz ready! Answer the questions below:")
                except:
                    st.error("Oops! SciBot had trouble creating the quiz. Try again!")
    
    # Display quiz if generated
    if st.session_state.current_quiz:
        quiz = st.session_state.current_quiz
        st.markdown(f"## 📚 {quiz.get('title', 'Science Quiz')}")
        st.markdown(f"*Difficulty level: {current_grade['level']}*")
        st.markdown("---")
        
        for i, q in enumerate(quiz.get('questions', [])):
            st.markdown(f"### Question {i+1}")
            st.markdown(f"**{q['question']}**")
            
            answer = st.radio(
                "Choose your answer:",
                q['options'],
                key=f"q_{i}",
                index=None
            )
            
            if answer:
                st.session_state.quiz_answers[i] = answer[0]  # Store just the letter (A, B, C, D)
            
            st.markdown("---")
        
        # Submit quiz button
        if st.button("📊 Submit Quiz", type="primary"):
            if len(st.session_state.quiz_answers) < len(quiz['questions']):
                st.warning("Please answer all questions before submitting!")
            else:
                # Calculate score
                correct = 0
                total = len(quiz['questions'])
                
                st.markdown("## 🎯 Quiz Results")
                
                for i, q in enumerate(quiz['questions']):
                    user_answer = st.session_state.quiz_answers.get(i, "")
                    correct_answer = q['correct']
                    
                    if user_answer == correct_answer:
                        correct += 1
                        st.markdown(f"""
                        <div class="correct-answer">
                            <strong>Question {i+1}: ✅ Correct!</strong><br>
                            {q['explanation']}
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class="wrong-answer">
                            <strong>Question {i+1}: ❌ Incorrect</strong><br>
                            You answered: {user_answer}<br>
                            Correct answer: {correct_answer}<br>
                            {q['explanation']}
                        </div>
                        """, unsafe_allow_html=True)
                    st.markdown("")
                
                score_percent = (correct / total) * 100
                st.markdown(f"### Final Score: {correct}/{total} ({score_percent:.0f}%)")
                
                # Update stats
                st.session_state.quizzes_taken += 1
                st.session_state.quiz_score += score_percent
                
                if score_percent == 100:
                    st.balloons()
                    st.success("🏆 Perfect score! You're a science superstar!")
                elif score_percent >= 80:
                    st.success("🌟 Great job! You really know your stuff!")
                elif score_percent >= 60:
                    st.info("👍 Good effort! Keep studying and you'll do even better!")
                else:
                    st.info("📚 Keep learning! SciBot is here to help you improve!")
                
                if st.button("🔄 Take Another Quiz"):
                    st.session_state.current_quiz = None
                    st.session_state.quiz_answers = {}
                    st.rerun()

# MODE 3: FLASHCARDS
elif mode == "🎴 Flashcards":
    st.markdown("### 🎴 Study with Flashcards!")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        flashcard_topic = st.text_input("What topic do you want flashcards for?", 
                                        placeholder=f"e.g., Parts of a Cell, Chemical Elements, Planets...")
    
    with col2:
        num_cards = st.slider("Number of Cards:", 5, 15, 10)
    
    if st.button("🎴 Generate Flashcards", type="primary"):
        if not api_key:
            st.warning("Please enter your API key first!")
        elif not flashcard_topic:
            st.warning("Please enter a topic for your flashcards!")
        else:
            with st.spinner("SciBot is creating your flashcards..."):
                system_prompt = f"""You are SciBot, creating educational flashcards.

CRITICAL - Grade Level Adjustment:
Student Grade Level: {current_grade['level']}
{current_grade['description']}
{current_grade['vocab']}

Create EXACTLY {num_cards} flashcards about: {flashcard_topic}

IMPORTANT: Adjust flashcard difficulty and vocabulary to match {current_grade['level']}:
- For younger grades: Simple terms, basic definitions, everyday examples
- For middle grades: Standard terms with clear explanations
- For older grades: Technical terms, detailed definitions, complex concepts

CRITICAL: Return ONLY valid JSON, nothing else. No markdown, no backticks.

Format:
{{
  "cards": [
    {{
      "front": "Question or term (grade-appropriate)",
      "back": "Answer or definition (2-3 sentences at {current_grade['level']} level)"
    }}
  ]
}}

Make them clear and educational at the appropriate level!"""
                
                prompt = f"Create {num_cards} flashcards about {flashcard_topic} for {current_grade['level']} level"
                
                response = call_scibot(prompt, system_prompt)
                
                try:
                    # Clean response
                    response = response.strip()
                    if response.startswith("```"):
                        response = response.split("```")[1]
                        if response.startswith("json"):
                            response = response[4:]
                    response = response.strip()
                    
                    flashcard_data = json.loads(response)
                    st.session_state.flashcards = flashcard_data.get('cards', [])
                    st.session_state.current_flashcard = 0
                    st.session_state.show_flashcard_answer = False
                    st.success("✅ Flashcards ready! Click on cards to flip them!")
                except:
                    st.error("Oops! SciBot had trouble creating flashcards. Try again!")
    
    # Display flashcards
    if st.session_state.flashcards:
        total_cards = len(st.session_state.flashcards)
        current = st.session_state.current_flashcard
        card = st.session_state.flashcards[current]
        
        # Progress
        st.progress((current + 1) / total_cards)
        st.markdown(f"**Card {current + 1} of {total_cards}** • *Level: {current_grade['level']}*")
        
        # Flashcard display
        if st.session_state.show_flashcard_answer:
            st.markdown(f"""
            <div class="flashcard">
                <h3>Answer:</h3>
                <h2>{card['back']}</h2>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="flashcard">
                <h3>Question:</h3>
                <h2>{card['front']}</h2>
                <p style="margin-top: 20px; font-size: 0.9em;">Click "Show Answer" to flip!</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Flashcard controls
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("⬅️ Previous", disabled=(current == 0)):
                st.session_state.current_flashcard -= 1
                st.session_state.show_flashcard_answer = False
                st.rerun()
        
        with col2:
            if st.session_state.show_flashcard_answer:
                if st.button("🔄 Show Question"):
                    st.session_state.show_flashcard_answer = False
                    st.rerun()
            else:
                if st.button("👁️ Show Answer"):
                    st.session_state.show_flashcard_answer = True
                    st.rerun()
        
        with col3:
            if st.button("➡️ Next", disabled=(current == total_cards - 1)):
                st.session_state.current_flashcard += 1
                st.session_state.show_flashcard_answer = False
                st.rerun()
        
        # Shuffle button
        if st.button("🔀 Shuffle Cards"):
            random.shuffle(st.session_state.flashcards)
            st.session_state.current_flashcard = 0
            st.session_state.show_flashcard_answer = False
            st.rerun()

# MODE 4: MY PROGRESS
elif mode == "📊 My Progress":
    st.markdown("### 📊 Your Learning Progress")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="❓ Questions Asked",
            value=st.session_state.questions_answered,
            delta="Keep asking!" if st.session_state.questions_answered > 0 else None
        )
    
    with col2:
        st.metric(
            label="📝 Quizzes Taken",
            value=st.session_state.quizzes_taken,
            delta="Great practice!" if st.session_state.quizzes_taken > 0 else None
        )
    
    with col3:
        if st.session_state.quizzes_taken > 0:
            avg_score = st.session_state.quiz_score / st.session_state.quizzes_taken
            st.metric(
                label="🎯 Average Score",
                value=f"{avg_score:.0f}%",
                delta="Awesome!" if avg_score >= 80 else "Keep practicing!"
            )
        else:
            st.metric(
                label="🎯 Average Score",
                value="--",
                delta="Take a quiz!"
            )
    
    st.markdown("---")
    
    # Show current grade level
    st.markdown(f"### 📚 Current Grade Level: {current_grade['level']}")
    st.info(f"SciBot is adjusting all explanations, quizzes, and flashcards to match {current_grade['level']}!")
    
    st.markdown("---")
    
    # Achievements
    st.markdown("### 🏆 Achievements")
    
    achievements = []
    
    if st.session_state.questions_answered >= 1:
        achievements.append(("🌱", "First Question", "Asked your first question!"))
    if st.session_state.questions_answered >= 10:
        achievements.append(("🌿", "Curious Learner", "Asked 10 questions!"))
    if st.session_state.questions_answered >= 25:
        achievements.append(("🌳", "Super Curious", "Asked 25 questions!"))
    
    if st.session_state.quizzes_taken >= 1:
        achievements.append(("📝", "Quiz Taker", "Completed your first quiz!"))
    if st.session_state.quizzes_taken >= 5:
        achievements.append(("📚", "Quiz Master", "Completed 5 quizzes!"))
    
    if st.session_state.quizzes_taken > 0:
        avg = st.session_state.quiz_score / st.session_state.quizzes_taken
        if avg >= 80:
            achievements.append(("⭐", "High Scorer", "Maintained 80%+ average!"))
        if avg == 100:
            achievements.append(("👑", "Perfect Student", "100% average score!"))
    
    if achievements:
        cols = st.columns(3)
        for i, (emoji, title, desc) in enumerate(achievements):
            with cols[i % 3]:
                st.markdown(f"""
                <div style="background-color: #f0f8ff; padding: 15px; border-radius: 10px; text-align: center; margin: 10px 0;">
                    <h1>{emoji}</h1>
                    <h4>{title}</h4>
                    <p style="font-size: 0.9em; color: #666;">{desc}</p>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("Start learning to unlock achievements!")
    
    st.markdown("---")
    
    # Motivational message from SciBot
    st.markdown("### 💬 Message from SciBot")
    
    if st.session_state.questions_answered == 0 and st.session_state.quizzes_taken == 0:
        message = "👋 Hi! I'm SciBot, your AI science tutor! I'm excited to help you learn! Start by asking me a question or taking a quiz!"
    elif st.session_state.questions_answered < 5:
        message = "🌟 You're off to a great start! Keep asking questions - that's how we learn!"
    elif st.session_state.quizzes_taken == 0:
        message = "📝 You've asked great questions! Why not test your knowledge with a quiz?"
    elif st.session_state.quizzes_taken > 0 and (st.session_state.quiz_score / st.session_state.quizzes_taken) >= 80:
        message = "🎉 Wow! You're doing amazing! Your hard work is really paying off!"
    else:
        message = "💪 Keep up the good work! Every question makes you smarter!"
    
    st.info(f"**SciBot says:** {message}")
    
    # Reset progress button
    st.markdown("---")
    if st.button("🔄 Reset All Progress"):
        st.session_state.questions_answered = 0
        st.session_state.quizzes_taken = 0
        st.session_state.quiz_score = 0
        st.success("Progress reset! Time for a fresh start! 🚀")
        st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 20px;">
    <p>🤖 <strong>SciBot</strong> - Your Friendly AI Science Tutor</p>
    <p style="font-size: 0.9em;">Created for 6th Grade Science Fair • Powered by Claude AI</p>
</div>
""", unsafe_allow_html=True)
