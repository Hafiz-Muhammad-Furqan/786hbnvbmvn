from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import os
from twilio.twiml.messaging_response import MessagingResponse
from spellchecker import SpellChecker
from fuzzywuzzy import process

app = Flask(__name__)

# Set up Gemini AI
GOOGLE_API_KEY = "AIzaSyCwSSey57mmeFF1dgizm-0tpJV-mJSzW70"
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# # Predefined responses and setup
# conversation_folder = 'saved_conversations'
# os.makedirs(conversation_folder, exist_ok=True)
# existing_files = os.listdir(conversation_folder)
# filenumber = max([int(f.split('.')[0]) for f in existing_files if f.endswith('.txt')], default=0) + 1
# file_path = os.path.join(conversation_folder, f'{filenumber}.txt')

# with open(file_path, 'w+') as file:
#     file.write('bot: Hello! Ask me anything about medicines, diseases, or drug interactions.\n')

predefined_responses = {
    "what are your interests": [
        "I'm interested in helping you medically!",
        "I have a wide range of interests and love learning new things!"
    ],
    "what is your number": [
        "You can contact the helpline at 123456."
    ],
    "what is your location": [
        "We are located at our official location.",
        "I'm offline, so I'm present at the same location as you."
    ],
    "where are you from": [
        "I exist in the digital world, but I am here to assist you!"
    ],
    "who is your father": [
        "I was created by the automated healthcare team."
    ],
    "who is your mother": [
        "I was created by the automated healthcare team."
    ],
    "what is your age": [
        "I was created in February 2025."
    ],
    "are you online?": [
        "No, I am completely offline."
    ],
    
    ### *Cold & Flu Responses*
    "my nose is choked": "That sounds like a symptom of a cold. Do you have a cold?",
    "yes i have cold": "You should take a Sudafed tablet after your meal.",
    "ok, i will take the sudafed tablet": "Let me know if you're feeling better after taking the Sudafed tablet.",
    "i took the sudafed tablet": "Good! Now, rest for a while and let me know if you feel better.",
    "no, i am still not feeling better after having sudafed tablet": "Okay, this might be more than a common cold. You should consult a doctor.",
    "can u book an appointment for me": "Yes, please provide the details in this format: 'Patient Name: Date: Doctor: Hospital:'",

    "i have a cough": "You should take a spoonful of Benadryl after your meal.",
    "ok, i will take the benadryl": "Let me know if you're feeling better after taking Benadryl.",
    "i took the dose of benadryl": "Good! Now, rest for a while and let me know if you feel better.",
    "no, i am still not feeling better after having benadryl": "This might not be a simple cough. You should consult a doctor.",

    "my chest is aching": "Chest pain can be a symptom of a cough. Do you have a cough?",
    "my nose is itching": "That sounds like a symptom of a cold. Do you have a cold?",
    "my throat is itching": "Throat itching could be related to a cough. Do you have a cough?",

    ### *Doctor Availability & Appointment Booking*
    "is a doctor available?": "Sorry, all doctors are occupied at the moment. We will connect you to a doctor soon. Would you like to book an appointment?",
    "hi can i see a doctor?": "All doctors are attending patients. We will get back to you soon. Would you like to book an appointment?",
    "i want to talk to a doctor": "You will be called once a doctor is available. Would you like to book an appointment?",
    "can you book an appointment with a doctor?": "Yes! Please provide the details in this format: 'Patient Name: Date: Doctor: Hospital.'",
    "thanks": "Happy to help!",

    ### *Fever & Weakness*
    "i am not feeling well": "Okay, can you tell me what's wrong? What are your symptoms?",
    "my body temperature has raised": "This sounds like a fever. You should take a tablet of Crocin after your meal.",
    "i am shivering": "Shivering can be a symptom of fever. You should take a Crocin tablet after your meal.",
    "i am feeling weak": "Weakness can be related to fever. You should take a Crocin tablet after your meal.",
    "i took crocin": "Good! Now, get some rest and let me know if you're feeling better.",
    "no, i am still not feeling better after having crocin": "This might not be a regular fever. You should consult a doctor.",
    
    ### *Pain & Injury*
    "my hand is aching": "Did you get hurt, or is it a sudden pain?",
    "my leg is aching": "Did you get hurt, or is it a sudden pain?",
    "my joint is aching": "Did you get hurt, or is it a sudden pain?",
    "yes i got hurt": "Is there swelling, physical deformity, or bleeding in the affected area?",
    "it is a mild ache": "Is there swelling, physical deformity, or bleeding in the affected area?",
    "yes there is swelling": "Swelling could indicate a fracture. Should I book an appointment for you?",
    "yes there is a physical deformity": "This could be a sign of a fracture. Should I book an appointment for you?",
    "yes it is bleeding": "If there's bleeding, you should see a doctor immediately. Should I book an appointment for you?",

    ### *Headache Types*
    "i have a headache": "What type of headache do you have? 1. Migraine - intense throbbing pain on one side of the head. 2. Cluster headaches - severe and recurrent headaches. 3. Tension headache - occasional dull pain.",
    "i have a migraine headache": "Migraines tend to be recurrent and may last up to 3 days. Would you like to talk to a doctor?",
    "i have a cluster headache": "Cluster headaches occur in daily clusters that can persist for weeks or months. Would you like to talk to a doctor?",
    "i have a tension headache": "Tension headaches can be triggered by stress, anxiety, or depression. Would you like to talk to a doctor?",

    ### *Greetings & General Chat*
    "hi there": "Hi! How are you feeling today?",
    "hello": "Hello! How are you feeling today?",
    "hi": "Hello! How are you feeling today?",
    "greetings!": "Hello! How are you feeling today?",
    "hi, how is it going?": "The app is working great! How are you feeling today?",
    "hi, nice to meet you.": "Thank you! You too. How are you feeling today?",
    "how do you do?": "I'm doing well. How are you feeling today?",
    "what's up?": "Not much! How are you feeling today?",
    "bye": "Bye! Nice talking to you.",
    "bye bye": "Goodbye! Thanks for using our service.",
    "thanks for helping me out": "You're most welcome!",
    "thanks": "Always happy to help!",

    ### *User Information Storage*
    "i live in city": "Okay, location stored. Welcome to the medical portal! Say Hi!",
    "my name is": "Hello! Your name has been stored. What is your age?",
    "my age is": "Okay, your age has been stored. Which city do you live in?",
    "i am years old": "Got it! Your age is stored. Which city do you live in?",
}

# Initialize spell checker with medical terms from predefined responses
spell = SpellChecker()
medical_words = set()
for key in predefined_responses.keys():
    medical_words.update(key.lower().split())
spell.word_frequency.load_words(list(medical_words))

# Slang corrections dictionary
slang_corrections = {
    "ur": "your", "u": "you", "thnks": "thanks", "pls": "please", "hv": "have",
    "coz": "because", "r": "are", "btw": "by the way", "asap": "as soon as possible",
    "tmrw": "tomorrow", "y": "why", "wht": "what", "n": "and", "da": "the",
    "dis": "this", "dat": "that", "lyk": "like", "lite": "light", "thru": "through",
    "gr8": "great", "luv": "love", "k": "okay", "omg": "oh my god", "fyn": "fine",
    "gud": "good", "msg": "message", "plz": "please", "ru": "are you", "wat": "what",
    "wen": "when", "wher": "where", "wich": "which", "wil": "will", "wud": "would",
    "yeh": "yes", "yup": "yes",
}

def correct_input(user_input):
    # Replace slang terms
    words = user_input.lower().split()
    corrected_slang = ' '.join([slang_corrections.get(word, word) for word in words])
    
    # Correct spelling
    corrected_words = []
    for word in corrected_slang.split():
        if word not in spell:
            corrected_word = spell.correction(word) or word
            corrected_words.append(corrected_word)
        else:
            corrected_words.append(word)
    return ' '.join(corrected_words).strip()

def get_predefined_response(user_input):
    corrected_input = correct_input(user_input)
    # Exact match check
    exact_match = predefined_responses.get(corrected_input, None)
    if exact_match is not None:
        return exact_match
    # Fuzzy match with threshold
    match = process.extractOne(corrected_input, predefined_responses.keys(), score_cutoff=80)
    return predefined_responses[match[0]] if match else None

# Custom AI Prompt
custom_prompt = """
You are a highly knowledgeable and compassionate medical assistant. Provide clear, accurate, and empathetic responses. 
Encourage consulting healthcare professionals for serious concerns. Keep responses concise (1-2 lines) unless detailed 
information is explicitly requested.
"""

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/get")
def get_bot_response():
    userText = request.args.get('msg', '').strip()
    if not userText:
        return "Enter a message."

    try:
        predefined = get_predefined_response(userText)
        if predefined:
            bot_reply = predefined[0] if isinstance(predefined, list) else predefined
        else:
            response = model.generate_content(f"{custom_prompt}\nUser: {userText}\nAssistant:")
            bot_reply = response.text.split("\n")[0].replace("*", "").strip() if response.text else "I’m not sure."

        # with open(file_path, "a") as log_file:
        #     log_file.write(f"user: {userText}\nbot: {bot_reply}\n")

        return bot_reply
    except Exception as e:
        return "Error occurred."

@app.route("/whatsapp", methods=['POST'])
def whatsapp_reply():
    user_message = request.form.get('Body', '').strip()
    if not user_message:
        return str(MessagingResponse().message("Invalid message."))

    try:
        predefined = get_predefined_response(user_message)
        if predefined:
            bot_reply = predefined[0] if isinstance(predefined, list) else predefined
        else:
            response = model.generate_content(f"{custom_prompt}\nUser: {user_message}\nAssistant:")
            bot_reply = response.text.split("\n")[0].replace("*", "").strip() if response.text else "I’m not sure."

        # with open(file_path, "a") as log_file:
        #     log_file.write(f"user: {user_message}\nbot: {bot_reply}\n")

        twilio_response = MessagingResponse()
        twilio_response.message(bot_reply)
        return str(twilio_response)
    except Exception as e:
        return str(MessagingResponse().message("Error occurred."))

if __name__ == "__main__":
    app.run(debug=True)