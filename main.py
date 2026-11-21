import random
import os
import anthropic
from dotenv import load_dotenv
load_dotenv()
START_MONEY = 1000
WIN_MONEY = 2500
BROKE_MONEY = 100
ROUNDS = 8
FEE = 2
companies = [
    {"name": "ByteBurger", "product": "Fast food", "price": 20, "jump": 0.01},
    {"name": "GreenLeaf", "product": "Healthy snacks", "price": 15, "jump": 0.015},
    {"name": "Zoomy Motors", "product": "Electric scooters", "price": 40, "jump": 0.02},
    {"name": "PixelPlay", "product": "Video games", "price": 30, "jump": 0.03},
    {"name": "RocketRide", "product": "Space tourism", "price": 60, "jump": 0.05},
]
for c in companies:
    c["start"] = c["price"]
    c["last"] = c["price"]
    c["change"] = 0
    c["owned"] = 0
    c["bankrupt"] = False
good_news = [
    "NAME's new product is a giant hit!",
    "Influencers can't stop talking about NAME!",
    "NAME wins Company of the Year!",
]
bad_news = [
    "Scandal at NAME! The boss is in big trouble.",
    "NAME recalls thousands of broken products.",
    "A fire shuts down NAME's main factory.",
]
cash = START_MONEY
history = []
rita = {"cash": START_MONEY, "owned": {}, "strategy": "", "picks": {}}
rita["scores"] = {"follow the hype": 0, "buy the dip": 0, "play it safe": 0, "go risky": 0}
RULES = """You are part of Market Mayhem, a stock market game for students aged 11-14.
All companies are made up and no real money is used.
Keep everything friendly and kid-safe. Never mention real companies, real people or real stock tips.
Only talk about this game and money basics. Use simple words."""
def ask_claude(prompt):
    if os.environ.get("ANTHROPIC_API_KEY", "") == "":
        return None
    try:
        client = anthropic.Anthropic()
        reply = client.messages.create(
            model="claude-haiku-5-5",
            max_tokens=1024,
            system=RULES,
            messages=[{"role": "user", "content": prompt}],
            output_config={"effort": "low"},
        )
        for block in reply.content:
            if block.type == "text":
                return block.text.strip()
    except Exception as error:
        print("(Claude didn't answer:", error, ")")
    return None
def my_money():
    total = cash
    for c in companies:
        total = total + c["owned"] * c["price"]
    return round(total, 2)
def rita_money():
    total = rita["cash"]
    for i in rita["owned"]:
        total = total + rita["owned"][i] * companies[i]["price"]
    return round(total, 2)
def new_price(c, shares):
    jump = c["jump"] * shares
    if jump > 0.4:
        jump = 0.4
    if jump < -0.4:
        jump = -0.4
    return round(c["price"] * (1 + jump), 2)
def ask_number(text):
    answer = input(text).strip()
    if answer.isdigit():
        return int(answer)
    return 0
def show_market():
    print()
    print("   Company        Price      Last round   You own")
    for i in range(len(companies)):
        c = companies[i]
        if c["bankrupt"]:
            print(f"{i + 1}  {c['name']:<14} BANKRUPT")
        else:
            print(f"{i + 1}  {c['name']:<14} ${c['price']:<9.2f} {c['change'] * 100:+6.1f}%      {c['owned']}")
    print(f"Cash: ${cash:.2f}   Total money: ${my_money():.2f}   Robo-Rita: ${rita_money():.2f}")
def pick_company():
    number = ask_number("Which company (1-5)? ")
    if number < 1 or number > len(companies):
        print("That's not a company.")
        return None
    if companies[number - 1]["bankrupt"]:
        print("That company is bankrupt!")
        return None
    return companies[number - 1]
def buy():
    global cash
    c = pick_company()
    if c is None:
        return
    amount = ask_number("How many shares? ")
    if amount < 1:
        return
    after = new_price(c, amount)
    cost = round((c["price"] + after) / 2 * amount + FEE, 2)
    if cost > cash:
        print(f"Not enough cash! That would cost ${cost:.2f}")
        return
    cash = round(cash - cost, 2)
    c["price"] = after
    c["owned"] = c["owned"] + amount
    print(f"You bought {amount} {c['name']} for ${cost:.2f}. The price went up to ${after:.2f}")
def sell():
    global cash
    c = pick_company()
    if c is None:
        return
    amount = ask_number("How many shares? ")
    if amount < 1:
        return
    if amount > c["owned"]:
        print(f"You only have {c['owned']} {c['name']}")
        return
    after = new_price(c, -amount)
    money = round((c["price"] + after) / 2 * amount - FEE, 2)
    cash = round(cash + money, 2)
    c["price"] = after
    c["owned"] = c["owned"] - amount
    print(f"You sold {amount} {c['name']} for ${money:.2f}. The price went down to ${after:.2f}")
def make_rumor():
    alive = []
    for i in range(len(companies)):
        if not companies[i]["bankrupt"]:
            alive.append(i)
    rumor = {"true": random.random() < 0.7, "by_claude": False}
    if random.random() < 0.1 or len(alive) == 0:
        rumor["company"] = None
        about = "the whole market"
        if random.random() < 0.5:
            rumor["text"] = "MARKET CRASH! Everyone is panicking."
            rumor["effect"] = -0.3
        else:
            rumor["text"] = "BOOM TIME! The whole market is buzzing."
            rumor["effect"] = 0.15
    else:
        i = random.choice(alive)
        rumor["company"] = i
        about = companies[i]["name"] + " (" + companies[i]["product"] + ")"
        if random.random() < 0.5:
            rumor["text"] = random.choice(good_news).replace("NAME", companies[i]["name"])
            rumor["effect"] = random.uniform(0.12, 0.3)
        else:
            rumor["text"] = random.choice(bad_news).replace("NAME", companies[i]["name"])
            rumor["effect"] = -random.uniform(0.12, 0.3)
    if rumor["effect"] > 0:
        mood = "GOOD"
    else:
        mood = "BAD"
    headline = ask_claude("Write a fun news headline for the game. It must be " + mood + " news about " + about + ". Idea: " + rumor["text"] + " Reply with only the headline, one line, max 14 words, no quotes.")
    if headline is not None:
        rumor["text"] = headline.split("\n")[0].strip('" ')
        rumor["by_claude"] = True
    return rumor
def coach(rumor):
    question = input("Ask Coach Claude a question: ")[:150]
    info = ""
    for c in companies:
        info = info + f"{c['name']}: price ${c['price']:.2f}, last round {c['change'] * 100:+.0f}%, player owns {c['owned']}\n"
    info = info + f"Player cash ${cash:.2f}, total ${my_money():.2f}. Goal ${WIN_MONEY}. Rumor: {rumor['text']}\n"
    prompt = "You are Coach Claude. Answer in 2 to 4 short sentences. Help the player think, don't give orders. Nobody can predict the market.\n"
    prompt = prompt + "Game right now:\n" + info + "Question: " + question
    answer = ask_claude(prompt)
    if answer is not None:
        print("Coach Claude (AI):", answer)
        log = open("coach_log.txt", "a", encoding="utf-8")
        log.write("Q: " + question + "\nA: " + answer + "\n")
        log.close()
        return
    biggest = companies[0]
    for c in companies:
        if c["owned"] * c["price"] > biggest["owned"] * biggest["price"]:
            biggest = c
    if my_money() < 300:
        print("Coach: Danger zone! Below $100 you're broke. Play it safe.")
    elif biggest["owned"] * biggest["price"] > my_money() * 0.7:
        print("Coach: Most of your money is in " + biggest["name"] + ". One crash and you could lose it all!")
    else:
        print("Coach: Spreading your money over different companies lowers your risk.")
def bots():
    riser = None
    cheapest = None
    for c in companies:
        if c["bankrupt"]:
            continue
        if riser is None or c["change"] > riser["change"]:
            riser = c
        if cheapest is None or c["price"] < cheapest["price"]:
            cheapest = c
        if c["change"] < -0.05:
            c["price"] = new_price(c, -3)
            print("Panic Pete sold 3 " + c["name"] + " because it dropped.")
    if riser is not None and riser["change"] > 0:
        riser["price"] = new_price(riser, 3)
        print("Hype Hannah bought 3 " + riser["name"] + " because it went up.")
    if cheapest is not None:
        cheapest["price"] = new_price(cheapest, 2)
        print("Bargain Bob bought 2 " + cheapest["name"] + " because it's the cheapest.")
def rita_pick(strategy):
    best = None
    for i in range(len(companies)):
        c = companies[i]
        if c["bankrupt"]:
            continue
        if best is None:
            best = i
        elif strategy == "follow the hype" and c["change"] > companies[best]["change"]:
            best = i
        elif strategy == "buy the dip" and c["change"] < companies[best]["change"]:
            best = i
        elif strategy == "play it safe" and c["jump"] < companies[best]["jump"]:
            best = i
        elif strategy == "go risky" and c["jump"] > companies[best]["jump"]:
            best = i
    return best
def rita_turn():
    for s in rita["scores"]:
        rita["picks"][s] = rita_pick(s)
    if rita["strategy"] == "" or random.random() < 0.25:
        rita["strategy"] = random.choice(list(rita["scores"]))
    else:
        best = "follow the hype"
        for s in rita["scores"]:
            if rita["scores"][s] > rita["scores"][best]:
                best = s
        rita["strategy"] = best
    pick = rita["picks"][rita["strategy"]]
    for i in list(rita["owned"]):
        if i != pick:
            c = companies[i]
            amount = rita["owned"][i]
            if not c["bankrupt"]:
                after = new_price(c, -amount)
                rita["cash"] = round(rita["cash"] + (c["price"] + after) / 2 * amount - FEE, 2)
                c["price"] = after
            del rita["owned"][i]
    print("Robo-Rita is using the strategy: " + rita["strategy"])
    if pick is None or pick in rita["owned"]:
        return
    c = companies[pick]
    amount = int(rita["cash"] * 0.5 / c["price"])
    if amount > 0:
        after = new_price(c, amount)
        cost = (c["price"] + after) / 2 * amount + FEE
        if cost <= rita["cash"]:
            rita["cash"] = round(rita["cash"] - cost, 2)
            c["price"] = after
            rita["owned"][pick] = amount
            print("Robo-Rita bought " + str(amount) + " " + c["name"])
def rita_learn():
    for s in rita["scores"]:
        i = rita["picks"][s]
        if i is not None:
            rita["scores"][s] = rita["scores"][s] * 0.6 + companies[i]["change"] * 0.4
def end_round(rumor):
    print()
    bots()
    rita_turn()
    if rumor["true"]:
        effect = rumor["effect"]
        news = "TRUE: " + rumor["text"]
    else:
        effect = -rumor["effect"] * 0.3
        news = "FAKE: " + rumor["text"]
    for i in range(len(companies)):
        c = companies[i]
        if c["bankrupt"]:
            continue
        price = c["price"]
        if rumor["company"] is None or rumor["company"] == i:
            price = price * (1 + effect)
        price = round(price * (1 + random.uniform(-c["jump"] * 2, c["jump"] * 2)), 2)
        if price < c["start"] * 0.25:
            price = 0
            c["bankrupt"] = True
            news = news + " " + c["name"] + " went BANKRUPT!"
        c["change"] = (price - c["last"]) / c["last"]
        c["price"] = price
        c["last"] = price
    rita_learn()
    return news
def show_history():
    print()
    print("HISTORY")
    for row in history:
        print(f"Round {row['round']}: {row['news']}")
        print(f"   Prices: {row['prices']}   You: ${row['money']:.2f}   Rita: ${row['rita']:.2f}")
print("=" * 55)
print("MARKET MAYHEM")
print("Buy and sell shares in 5 companies. Every trade moves the price!")
print(f"Reach ${WIN_MONEY} to win. Drop below ${BROKE_MONEY} and you're broke.")
print(f"Each trade costs ${FEE}. Beat Robo-Rita, the AI that learns!")
print("=" * 55)
status = "finished"
round_number = 1
while round_number <= ROUNDS:
    rumor = make_rumor()
    print()
    print("=" * 55)
    print(f"ROUND {round_number} of {ROUNDS}")
    if rumor["by_claude"]:
        print("RUMOR (written by Claude AI): " + rumor["text"])
    else:
        print("RUMOR: " + rumor["text"])
    print("Rumors are only true 70% of the time...")
    while True:
        show_market()
        choice = input("(b)uy, (s)ell, (c)oach, (h)istory, (n)ext round: ").strip().lower()
        if choice == "b":
            buy()
        elif choice == "s":
            sell()
        elif choice == "c":
            coach(rumor)
        elif choice == "h":
            show_history()
        elif choice == "n":
            break
        else:
            print("Type b, s, c, h or n")
    news = end_round(rumor)
    print("NEWS: " + news)
    prices = ""
    for c in companies:
        prices = prices + c["name"] + " $" + str(c["price"]) + "  "
    history.append({"round": round_number, "news": news, "prices": prices, "money": my_money(), "rita": rita_money()})
    if my_money() >= WIN_MONEY:
        status = "won"
        break
    if my_money() < BROKE_MONEY:
        status = "broke"
        break
    if rita_money() >= WIN_MONEY:
        status = "rita won"
        break
    round_number = round_number + 1
show_history()
print()
print("=" * 55)
if status == "won":
    print(f"YOU WIN! You reached ${my_money():.2f}!")
elif status == "broke":
    print("YOU WENT BROKE! Game over.")
elif status == "rita won":
    print("Robo-Rita reached the goal first. She wins!")
elif my_money() > rita_money():
    print(f"Game over! You beat Robo-Rita with ${my_money():.2f}!")
else:
    print(f"Game over! Robo-Rita wins with ${rita_money():.2f}. You had ${my_money():.2f}.")
print("=" * 55)
