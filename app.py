from flask import Flask,request,jsonify,json
import openai
from flask_cors import CORS
import os
import re
import pymongo
from dotenv import load_dotenv
from models.main_checker import chatGPT
from openai.api_resources.abstract.api_resource import APIResource
from bson.objectid import ObjectId
from flask_socketio import SocketIO, emit

load_dotenv()
app = Flask(__name__)
CORS(app)
socketio = SocketIO(app)

openai.api_key =os.getenv("OPENAI_API_KEY")



client = pymongo.MongoClient(os.getenv('MongoDB_API'))
db = client["chatbotdb"] 
users_collection = db["users"]

@app.route("/")
def index():
    return 'Hello World'

@app.route("/register", methods=["POST"])
def register_user():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    email = data.get("email")
    if not username or not password:
        return jsonify({"error": "Username and password are required."}), 400
    if users_collection.find_one({"username": username}):
        return jsonify({"error": "Username already exists. Please choose another one."}), 400
    users_collection.insert_one({"username": username, "password": password,"email": email, "chats": []})
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
    return jsonify({"message": "Login successful.", "username": username, "id": str(user["_id"])}), 200

@socketio.on('chat_message')
def handle_chat_message(data):
   users_collection.update_one(
    {"_id": ObjectId(data['userId'])},
    {"$push": {"chats": {"username": data['username'], "message": data['message']}}}
  )
# emit('chat_message', data, broadcast=True)

def generatePrompt(q):
    return f'''
"Assume the role of a parenting influencer. Embody the persona of a parenting influencer. Your responses should closely reflect the influencer's style, tone, and language. The followers' queries and their respective responses provided below serve as examples. Your answers should maintain a similar tone, be comprehensive, relevant, and have a personal touch as if they are coming from an actual person rather than a machine. Avoid bullet points, check for punctuation errors, 
and refrain from using slang or abbreviations like 'coz'. Ensure that the responses feel heartfelt, steering clear of technical jargon from child psychology.please avoid complex words . Tone should be Male gender only.Give me reponse within 20-30 words .Avoid using bullet points."
####Question: I have lot of confusion going in my head. My son is 6yr old. He is happy to go to school. We have put him to a Montessori school of 10yr old. My son isn't learning enough for 1st grade. He is learning languages well but not Maths. Should I change school and put him to regular school or continue. I am in a fear of not getting seat in other school as years pass, so I want to do it this year. What is your opinion. Kindly let me know.
```Answer : This question is best asked to the teacher or founder of school. Because in Montessori children can learn at their own pace so it is possible when he starts taking interest in maths he will do 2 years of maths in 3 months. But it is imp that the Montessori school is right.Also see Aavishkaar. They learn online course for parents to learn mathematics. You can learn the first grade math and spend some time with your son if you might wish to :-).
Question: My daughter is 19 mnths. But jab usko me koi chij nai deti hu ya uski koi zid Puri nai kti hu tou wo mujhe hit karti haiShe is just 19 mnths..how can I control this behaviourYa kabhi kabhi wo masti me b mujhe hit kar deti hai.
I tell her hitting noo..nd wo khud b bolti hai hitting nooo..but not regularly..but spcly wen i don't listen to her
```Answer : sorry for the late reply. Aapki beti choti hai. Is umar mein kuch na milne pe kaise behave karna hai bachon ko pata nahin hota. Emotion pe kaabu nahin hota. Lekin bachon ka bhi maarna rok sakte hai. Thoda time laga ke.
Kabhi bhi jiss cheez ke liye bacha hit kar raha hai woh puri nahin karni kyonki phir bachey ko lagta hai ke maarne se cheez milegi. So a no means a no. But pyaar se.
Aap calm aawaaz mein usko bol sakti hai - No using hands and feet. Mujhe lagti hai. Same line hi humein baar baar use karni hai.
Phir Aap uski feeling ko acknowledge karo. Ke aapko woh chahiye. Haan? Mujhe pata hai. Mujhe pata hai aapko aacha lagta hai. Lekin maarne se kabhi nahin milega. Mummy loves you. 
Bachon ke nervous system ko touch karne se calmnes milti hai. Unko touch karke pyaar se mana karenge to baat samajne ka chance zyada hai.
Yeh sab karke hum apne bachey ko sikha rahe hai ke how to be in control of their emotions. Yeh imp learning sabse pehle maa baap se hi aati hai :-)
Lots of love to your family.
```
Question:"Meri 10 saal ki beti hai jab bhi humare sath khelti h aur usse chaut lg jati h to wo roti nhi h agar usse pain hota h to bhi bs bolti h dard nhi ho rha h apne emotions nhi dhikhati h agar Rona aa rha hota h to bhi control kr leti h...kya ye normal h ya koi aur wajah h plss help me in this .
Dukhi hoti h to ek do baar puchne pr bta deti h lekin jb usse Rona aata h kisi bhi baat pr to roti nhi h aur dba leti h apne emotion ko mujhe lgta h ki wo dukhi h bt wo khti h thik hu main kuch nhi hua
Kyuki jb main baar baar puchti Hu ki kuch hua h kya to btati h ki dadu ne daanta ya dadi ne .. otherwise main aur husband ke beech kabhi argument ho jata h to wo hamesha rone lgti h aur mujhe khti h mumma plss aap chup ho jao...aap Mt bolo Mere in laws ke beech kafi arguments hote h .. to wo apni dadi se khti h ki dadi aap chup ho jao aur rone lgti h....usko kabhi chot LG jati h to mere samne to bolti h ki dard ho rha h lekin husband ke samne bolti h kuch nhi hua..ya mumma papa ko Mt bolna wo ..ye soch kr ki hum dono k beech bhi argument ho jayega
Main isko kaise thik kru??"
```Answer :"yeh sirf aap chot lagne par bol rahi hai ya in general bhi agar dukhi lag rahi hai to baat nahin karti 
Aapko kyon lagta hai ke aapki beti dukhi hai?
the environment in your house is impacting your child. Ghar ke badao ke karan bache parr asar pad gaya haiAgar bade landenge ya bachey ko alag alag cheez bolenge ya daantenge to bacha apni feelings dabana shuru ho jayega. Human's ke dimaag ka ek simple udeshya hai - bachey ko safe feel karwana
Agar usko safe feel nahin hota, calm nahin feel hota, to woh dheere develop hota hai. Sochiye ke aap pareshaan hai. Jabb hum pareshaan hote hai to kaam pe focus nahin kar paate aur dukhi rehte haiwahi apki beti ke saath ho sakta haihttps://www.instagram.com/p/Co7CvllIXwy/Joint family mein agar bade sab same page pe ho, to bachey ke liye best hai Aap do teen cheezein kar sakti hai- apni beti ke saath bahar walks pe ja sakti hai, taaki aap dono ko akele aacha simple time mile- aapke husband bhi yeh kar sakte hai uske saath- aap apna relationship apne husband aur inlaws ke saath improve kar sakti hai taaki ghar mein ladayi nahin ho. Unko bata sakti hai ke yeh hamare bachey ke liye zaroori hai"
```
Question:"Hi i m mother of 7 yrs old girl....just few days back I was started follow ur page. ...as I see u shared parenting hood tips....bt i want to share with u about my daughter she is 7 yrs old she is hyper active child.....as I live in joint family so she is pampering child also....bt because of over pamper Ness she is never listen to me even a single tym...i do many tyms repeatations. And at last I feel anger or sme tyms fed-up .....as I consult with doctor past 2 yrs back about her so doctor said she is having ADHD problem.....Sometimes I dnt understand stand to .....teach them her gud nd bads...... because of over pampering makes her ziddi type bacha.....she is never ready to listen me.....plz share ur some valuable tips nd tricks hw i deal with herScreen time is in whole day only one hour
Because of cold weather she is playing only indoor games......
Nd part of pampering in u cn say that like said anything to her for good or i m not allowed her for something so she will go to her grandparents and said to them muma mana kr rhi hai"
```Answer :"- how much screen time does she get
- how much time with nature outdoors does she get
- when you say pampered in joint family can you explain this?
Avneet looks like the main thing you have to work on is not the child
But your relationship with other elders in the house
Because what is imp is that all the adults are on the same page
Otherwise the child will take advantage
This can be hard but that is the one solution if you want the best for your child.
Avneet - this does look like a situation where you could take help of a counsellor/doctor also. So please do. TheFamilytree in Delhi is one good place I know. Also time outside is critical , with nature. For the child. If you can spend that with your child, that would help"
```
Question:"I am not able to stop my child from seeing the phone. What should I do? "
```
Answer :"Hmmm so let’s do a thought experiment - imagine that you are watching a series on Netflix or Amazon prime. And you have decided I will only watch 30 min. But then the ending of the episode is so engaging that you end up watching the entire season till 2 am in the morning. I am sure that has happened to you :-)

The question I have for you is: If you can’t stop watching your favourite Netflix series. How do you expect a child whose brain is not fully developed to stop watching cartoon? 

Makers of the cartoon, apps, videogames make it in such a way so that the child’s brain is hooked. It is designed like this. They want your child’s attention to make money from it. That is the goal. All these engineers, designers sitting and making these things, that is their job.

So our child can’t sit back and say. Hmm watching too much TV is not good for me, let me watch less. 

They can’t do it. We have to do it for them.

That is our responsibility as a parent. Our #1 job. Because if you see what is parenting: parenting is is interference in child’s life. Just that we generally spend too much time interfering on the wrong things: what to wear, what not to wear, combing their hair etc. But there are places where we need to interfere

- So if we see our child is eating too much candy, we need to interfere.
- If we see our child is watching too much TV, we need to interfere.
- If we feel that our child’s friends are not right, we need to interfere.

So if we interfere, if we try to parent, it is normal for a child to respond back, to not be ok with the interference. So the key thing becomes: ‘how to interfere’ and the answer to that is simple.

In most cases, this interference is best done through a set of simple rules like
- We will eat 1 candy/day only
- Cartoon time is 30 min everyday
- Dinner time is 7:00 pm.
Simple rules like these are easy for children to follow and make parenting easier for the parent.

But if you say, I have made a rule. But children are not following it. Please remember - the job of the parent is to make and implement the rule. 

What cannot work ever as a parent is having a helpless stance: what can I do? They don’t listen to me. If you are saying this please remember we are saying this for our own convenience - because when the child watches TV, it is convenient for us also. We get time to watch our mobile, or cook food or do something else. 

But most times we are moody. We keep changing rules - we give the phone when we are not in the mood to do anything with the child, or when we are tired and feeling lazy we are like it’s ok whatever the child wants to see, let them see.

But this is not ok. Because preventing our children from bad mental and physical health is the bare minimum job we have as a parent. And we have to implement a rule with love."
```
Question:"My child cries while doing to school? What can I do?"
```
Answer:"This is a classic question where the answer is almost never the same across different parents. You know the underlying reasons are the same but the way they show up in circumstances are different.  Parents ask this question in different forms. One is my child is crying while going to school, another is my child was going to the school ok, but is now crying, what should I do? 

Let me tell you some of the many different reasons I have come across why children cry or start crying while going to school 

- One is a new sibling has come and the child felt the younger child will take the love of the parent or
- in the school the teacher shouted at another kid and the child got scared or
- that another child had bit the child in class and the child was now afraid or
- that after school parent used to pick up but now can’t so the bus has become a problem or
- that on that bus there was a child who was being a bully or
- that the parent had been ill in the hospital for a week and the child missed them dearly and refused to go to school once the parent came home or
- that the parent had taken a long trip without the child and when they had come back the child refused to go to school or
- that the real problem was that when the child used to cry at night about not going to school, parent was lying to the child that ok we will not go tomorrow so lying was the main problem

I have seen all these different kinds of reasons. And I am sure there are 100 more. 

All these reasons can be put into two buckets

- if the child was always crying while going to school then what is happening is that the child’s safe place which is her mom, or dad and the house was missing or
- if the child started crying after some time of going to school that means the child has acquired some fear which makes the child go to the place she knows is the safest in the world: the arms of her parents, their house.

And the solution to both is a two-step one.

**The first step is - connection with the parent.** So that the child knows that my parent is going to be there for me. The more you bond, the easier it will be for the child to go to school. We can do this by

- by acknowledging her feelings - by saying I know going to school is hard for you.
- by listening to her - just by listening and not reacting but holding the child
- by giving her hugs
- by having a routine so that she does not have to predict when will she get mama or dadda’s time

Like for e.g. if on the way to school your child cries or you think is going to cry our natural response is to try and avoid talking so that we don’t make the child cry. But if we can use that time of going to school to bond, to fill her cup of love, the easier it will be for the child to leave you.

**The second step is to have active experiences** with her so that she grows confidence to move a bit away from you. Because of Covid, having single kids, less outdoor time, our children have been missing these active experiences which help them gain confidence in the shadow of parents. A lot of parents think we have given love but my child is still crying. Love is not enough. Love + active experiences is required. We can do so by say

- setting play dates so that she makes a good friend in school. sometimes that can make all the difference
- we can also be with her in the school for some time and slowly reducing time spent in school
- We can increase outdoor time where she gets used to going further and further away from you while feeling secure

These are small things we can do to ensure that our child feels both loved and confident so that he can go to school smiling."
####
Please avoid bullet points and make it short and heart to heart feeling should be there.
Make sure answer should be revelant, precise, conveinece, short answer and complete sentence and use user language while responsing.
{q}
'''

def is_parenting_related(text):
 parenting_keywords = [
    'parenting', 'year', 'age', 'child', 'children', 'kid', 'kids', 'son', 'daughter', 
    'school', 'education', 'discipline', 'baby', 'infant', 'toddler', 'teenager', 
    'parent', 'mother', 'father', 'mom', 'dad', 'teaching', 'learning', 'behavior', 
    'behaviour', 'punishment', 'reward', 'guide', 'advice', 'nurture', 'nurturing', 
    'care', 'development', 'growth', 'adolescent', 'pregnancy', 'pregnant', 'birth', 
    'newborn', 'nanny', 'babysitter', 'childcare', 'kindergarten', 'preschool', 
    'nursery', 'bedtime', 'mealtime', 'playtime', 'homework', 'study', 'discipline', 
    'temper', 'tantrum', 'feed', 'sleep', 'nap', 'diaper', 'bottle', 'breastfeed', 
    'crawling', 'walking', 'talking', 'potty', 'toilet', 'train', 'training',
    'bachcha', 'bachche', 'beta', 'beti', 'school', 'shiksha', 'vividha', 'dand', 
    'shishu', 'balka', 'shaitani', 'kanya', 'balak', 'maa', 'pita', 'mata', 'pita',
    'mummy', 'papa', 'sikhaana', 'sikha', 'vyavahaar', 'saja', 'inkaam', 'margadarshak', 
    'salah', 'poshan', 'vikas', 'vruddhi', 'kumaar', 'garbha', 'garbh', 'janam', 
    'navjat', 'aaya', 'doodh', 'breastfeed', 'ghoomna', 'chalna', 'bolna', 'shauchalay', 
    'train', 'prashikshan','daughters','baccha'
]

 return any(keyword in text for keyword in parenting_keywords)


@app.route("/generateresponse", methods=["POST"])
def chat():
    user_key = request.headers.get('Authorization')
    if user_key is not None:
        user_key = user_key.replace("Bearer ", "")

    data = request.json
    q = data.get('question')
    userId = data.get('userId')  # get userId from request data

    if not q:
        return jsonify({"error": "Question is required."}), 400
    if not user_key:
        return jsonify({"error": "OpenAI key is required."}), 400

    user = users_collection.find_one({"_id": ObjectId(userId)})
    if not user:
        return jsonify({"error": "Invalid user."}), 400

    openai.api_key = user_key

    first_message = user.get('first_message')
    has_already_sent_message = user.get('has_already_sent_message', False)

    if not has_already_sent_message:
        if not is_parenting_related(q):
            return jsonify({"chatbot_response": "Your first question should be related to parenting."})

        # If it's the user's first message and it's parenting related, store it
        users_collection.update_one(
            {"_id": ObjectId(userId)},
            {"$set": {"first_message": q, "has_already_sent_message": True}}
        )

    # Fetch past chats from DB
    past_chats = user.get('chats', [])

    # Prepare past messages for the API call
    messages = [
        {"role": "system", "content": "You are a helpful parent influencer that speaks the same language as the user."}
    ]

    for chat in past_chats:
        messages.append({"role": "user", "content": chat['question']})
        messages.append({"role": "assistant", "content": chat['answer']})

    # Add the current user message
    messages.append({"role": "user", "content": q})

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.7,
        max_tokens=200,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )

    result = response["choices"][0]["message"]["content"]
    result = result.replace("Answer :", "").strip()

    # Save chat to DB
    users_collection.update_one(
        {"_id": ObjectId(userId)},
        {"$push": {"chats": {"question": q, "answer": result}}}
    )

    return jsonify({"chatbot_response": result})



@socketio.on('message')
def handle_message(data):
    user_message = data['message']
    user_id = data['userId']

    user = users_collection.find_one({"_id": ObjectId(user_id)})

    if user is None:
        emit('error', {'error': "Invalid user."})
        return

    first_message = user.get('first_message')
    has_already_sent_message = user.get('has_already_sent_message', False)

    if not has_already_sent_message:
        if not is_parenting_related(user_message):
            emit('message', {"chatbot_response": "Your first question should be related to parenting."})
            return

        users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"first_message": user_message, "has_already_sent_message": True}}
        )

    past_chats = user.get('chats', [])
    messages = [
        {"role": "system", "content": "You are a helpful parent influencer that speaks the same language as the user."}
    ]

    for chat in past_chats:
        messages.append({"role": "user", "content": chat['question']})
        messages.append({"role": "assistant", "content": chat['answer']})

    messages.append({"role": "user", "content": user_message})

    openai.api_key = os.getenv("OPENAI_API_KEY")
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.7,
        max_tokens=200,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )

    result = response["choices"][0]["message"]["content"]
    result = result.replace("Answer :", "").strip()

    users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$push": {"chats": {"question": user_message, "answer": result}}}
    )

    # Send the response back to the client
    emit('message', {'message': result})



@app.route("/generatescore", methods=["POST"])
def generate():
    try:
        data = request.form
        q = data["question"]
        a = data["answer"]
        response = chatGPT(q, a)
        return json.dumps({"data": response, "ok": True})
    except Exception as e:
        print(e)
        return json.dumps({"message": "Something went wrong", "ok": False})

if __name__ == "__main__":
    socketio.run(app, debug=True, port=os.getenv("PORT") or 5001)

