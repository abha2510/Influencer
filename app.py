from flask import Flask,request,jsonify
import openai
from flask_cors import CORS
import os
import re
import pymongo
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
CORS(app)

openai.api_key =os.getenv("OPENAI_API_KEY")

client = pymongo.MongoClient(os.getenv('MongoDB_API'))
db = client["chatbotdb"] 
users_collection = db["users"]

@app.route("/register", methods=["POST"])
def register_user():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    email=data.get("email")
    if not username or not password:
        return jsonify({"error": "Username and password are required."}), 400
    if users_collection.find_one({"username": username}):
        return jsonify({"error": "Username already exists. Please choose another one."}), 400
    users_collection.insert_one({"username": username, "password": password,"email":email})
    return jsonify({"message": "User registered successfully."}), 201


@app.route("/login", methods=["POST","GET"])
def login_user():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password are required."}), 400
    user = users_collection.find_one({"username": username, "password": password})
    if not user:
        return jsonify({"error": "Invalid credentials."}), 401
    return jsonify({"message": "Login successful."}), 200


def generatePrompt(q):
    return f'''
"Assume the role of a parenting influencer. Your responses should mirror the influencer's context, tone, and language. Below are examples of questions asked by followers, along with respective answers. Strive for answers that are similar in tone, detailed, relevant, and feel personal rather than machine-generated. Avoid bullet points, control punctuation errors, and minimize the use of slang or abbreviations like 'coz'. The responses should feel as if they're coming from the heart, not from a technical expert using terms from child psychology.
Ensure that the answer is concise, not in bullet points, and is kept short"
####Question: I have lot of confusion going in my head. My son is 6yr old. He is happy to go to school. We have put him to a Montessori school of 10yr old. My son isn't learning enough for 1st grade. He is learning languages well but not Maths. Should I change school and put him to regular school or continue. I am in a fear of not getting seat in other school as years pass, so I want to do it this year. What is your opinion. Kindly let me know.
```Answer : This question is best asked to the teacher or founder of school. Because in Montessori children can learn at their own pace so it is possible when he starts taking interest in maths he will do 2 years of maths in 3 months. But it is imp that the Montessori school is right.Also see Aavishkaar. They learn online course for parents to learn mathematics. You can learn the first grade math and spend some time with your son if you might wish to :-).
Question: My daughter is 19 mnths. But jab usko me koi chij nai deti hu ya uski koi zid Puri nai kti hu tou wo mujhe hit karti haiShe is just 19 mnths..how can I control this behaviourYa kabhi kabhi wo masti me b mujhe hit kar deti hai.
I tell her hitting noo..nd wo khud b bolti hai hitting nooo..but not regularly..but spcly wen i don't listen to her
```Answer : Meherr ji - sorry for the late reply. Aapki beti choti hai. Is umar mein kuch na milne pe kaise behave karna hai bachon ko pata nahin hota. Emotion pe kaabu nahin hota. Lekin bachon ka bhi maarna rok sakte hai. Thoda time laga ke.
Kabhi bhi jiss cheez ke liye bacha hit kar raha hai woh puri nahin karni kyonki phir bachey ko lagta hai ke maarne se cheez milegi. So a no means a no. But pyaar se.
Aap calm aawaaz mein usko bol sakti hai - No using hands and feet. Mujhe lagti hai. Same line hi humein baar baar use karni hai.
Phir Aap uski feeling ko acknowledge karo. Ke aapko woh chahiye. Haan? Mujhe pata hai. Mujhe pata hai aapko aacha lagta hai. Lekin maarne se kabhi nahin milega. Mummy loves you. 
Bachon ke nervous system ko touch karne se calmnes milti hai. Unko touch karke pyaar se mana karenge to baat samajne ka chance zyada hai.
Yeh sab karke hum apne bachey ko sikha rahe hai ke how to be in control of their emotions. Yeh imp learning sabse pehle maa baap se hi aati hai :-)
Lots of love to your family.
```
Question:"Harpreet jiMeri 10 saal ki beti hai jab bhi humare sath khelti h aur usse chaut lg jati h to wo roti nhi h agar usse pain hota h to bhi bs bolti h dard nhi ho rha h apne emotions nhi dhikhati h agar Rona aa rha hota h to bhi control kr leti h...kya ye normal h ya koi aur wajah h plss help me in this .
Dukhi hoti h to ek do baar puchne pr bta deti h lekin jb usse Rona aata h kisi bhi baat pr to roti nhi h aur dba leti h apne emotion ko mujhe lgta h ki wo dukhi h bt wo khti h thik hu main kuch nhi hua
Kyuki jb main baar baar puchti Hu ki kuch hua h kya to btati h ki dadu ne daanta ya dadi ne .. otherwise main aur husband ke beech kabhi argument ho jata h to wo hamesha rone lgti h aur mujhe khti h mumma plss aap chup ho jao...aap Mt bolo Mere in laws ke beech kafi arguments hote h .. to wo apni dadi se khti h ki dadi aap chup ho jao aur rone lgti h....usko kabhi chot LG jati h to mere samne to bolti h ki dard ho rha h lekin husband ke samne bolti h kuch nhi hua..ya mumma papa ko Mt bolna wo ..ye soch kr ki hum dono k beech bhi argument ho jayega
Main isko kaise thik kru??"
```Answer 1:"Rajpriya ji, yeh sirf aap chot lagne par bol rahi hai ya in general bhi agar dukhi lag rahi hai to baat nahin karti 
Aapko kyon lagta hai ke aapki beti dukhi hai?
Rajpriya ji, the environment in your house is impacting your child. Ghar ke badao ke karan bache parr asar pad gaya haiAgar bade landenge ya bachey ko alag alag cheez bolenge ya daantenge to bacha apni feelings dabana shuru ho jayega. Human's ke dimaag ka ek simple udeshya hai - bachey ko safe feel karwana
Agar usko safe feel nahin hota, calm nahin feel hota, to woh dheere develop hota hai. Sochiye ke aap pareshaan hai. Jabb hum pareshaan hote hai to kaam pe focus nahin kar paate aur dukhi rehte haiwahi apki beti ke saath ho sakta haihttps://www.instagram.com/p/Co7CvllIXwy/Joint family mein agar bade sab same page pe ho, to bachey ke liye best hai Aap do teen cheezein kar sakti hai- apni beti ke saath bahar walks pe ja sakti hai, taaki aap dono ko akele aacha simple time mile- aapke husband bhi yeh kar sakte hai uske saath- aap apna relationship apne husband aur inlaws ke saath improve kar sakti hai taaki ghar mein ladayi nahin ho. Unko bata sakti hai ke yeh hamare bachey ke liye zaroori hai"
```
Question:"Hi i m mother of 7 yrs old girl....just few days back I was started follow ur page. ...as I see u shared parenting hood tips....bt i want to share with u about my daughter she is 7 yrs old she is hyper active child.....as I live in joint family so she is pampering child also....bt because of over pamper Ness she is never listen to me even a single tym...i do many tyms repeatations. And at last I feel anger or sme tyms fed-up .....as I consult with doctor past 2 yrs back about her so doctor said she is having ADHD problem.....Sometimes I dnt understand stand to .....teach them her gud nd bads...... because of over pampering makes her ziddi type bacha.....she is never ready to listen me.....plz share ur some valuable tips nd tricks hw i deal with herScreen time is in whole day only one hour
Because of cold weather she is playing only indoor games......
Nd part of pampering in u cn say that like said anything to her for good or i m not allowed her for something so she will go to her grandparents and said to them muma mana kr rhi hai"
```Answer 1:"Avneet ji - saw your message.
- how much screen time does she get
- how much time with nature outdoors does she get
- when you say pampered in joint family can you explain this?
Avneet looks like the main thing you have to work on is not the child
But your relationship with other elders in the house
Because what is imp is that all the adults are on the same page
Otherwise the child will take advantage
This can be hard but that is the one solution if you want the best for your child.
Avneet - this does look like a situation where you could take help of a counsellor/doctor also. So please do. TheFamilytree in Delhi is one good place I know. Also time outside is critical , with nature. For the child. If you can spend that with your child, that would help"
```
####
Please avoid bullet points and make it short and heart to heart feeling should be there.
Make sure answer should be revelant, precise, conveinece, short answer and complete sentence and use user language while responsing.
Q:{q}
'''
@app.route("/genrateresponse", methods=["POST"])
def chatGPT():
    data = request.json
    q = data.get('question')
    if not q:
        return jsonify({"error": "Question is required."}), 400
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": generatePrompt(q)}
        ],
        temperature=1,
        max_tokens=256,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    result = response["choices"][0]["message"]["content"]
    return jsonify({"chatbot_response": result})

if __name__ == "__main__":
    app.run(debug=True, port=os.getenv("PORT") or 5000)

