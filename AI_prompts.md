# Homework 4 AI Prompts

## Problem 1: Vibe coder prompts

**Prompt (my own words):**

> Problem 1 instructs me to create AI_prompts.md at the start of the assginment and update it as I go. It is a log of what I type to you. I need one section for each problem. The sections need to include:
> -problem number and title
> -at least one prompt typed in my own words
> -one follow-up prompt if needed and one sentence on what was lacking in the first.
>
> Go ahead and do this for problems 1 and 13. I'll update problem 13 when I get to the end again. My standard practice is to figure out what I need to end up with, then come back to the start and start there.

**Follow-up prompt:** None needed.

## Problem 2: Analyze the database

**Prompt (my own words):**

> Problem 2: Analyze the database
>
> I am supposed to look at the database and understand each table's fields. I will tell you when I am  done, then, I want you (Claude) to do the same).
>
> Focus on understanding catalogue, inventory, and users
>
> Create output/harness.md
>
> Each table and its fields needs to be in there with one short line on why the individual fields matter for the shop. I'll keep growing this harness file.
>
> Before you do anything, do you understand the challenge? I want to make a beautiful customer website for Campus Customs with a helpful chatbot. React + Vite TypeScript front end and a Python FastAPI backed w/ a PydanticAI agent brain. Shoppers will browse products, create an account, chat about merchandise, see matching items, and get honest answers about the price and stock from a local database (when it comes time to update in harness, it's going to be told it can never hallucinate price or inventory data)
>
> I have a database with prodcut catalogue, the inventory by size, and users w/ hashed passwords. there are also product image files. i'm supposed to match it to (https://yalebulldogblue.com/) for styling - maybe not match, but research for styling - and info for the agent prompt.

**Follow-up prompt:**

> ok, I read all the tables. I see what's going on there.
>
> catalogue - has all of our product info
> inventory - tells how much of each product and what size we have
> users - the individual accounts (looks like we need admin and shoppers)
> chat messages - i think this was the professor training a chatbot
> sqlite sequence - not sure what this is

**What the first prompt lacked:** It held Claude back until I had explored the database myself, so the follow-up was needed to give my own read of each table and tell Claude to start its analysis.

## Problem 3: Build the Campus Customs website

**Prompt (my own words):**

> Problem 3: Build the Campus Customs website
>
> Now, I need you to scaffold a React + Vite + TypeScript front end for the Campus Customs store. It needs a nav bar w/ links to the main pages:
> -Home
> -Products
> -About Us
> -Log in
> -Create account
>
> The wording needs to be pulled from yalebulldogblue.com for Home and About Us but MUST be written in my own voice and not copied from the original site text.
>
> The products page needs to have:
> -product images from the catalogue - there are image paths in the db
> -basic product info, such as name, price, and short dsecription
>
> each prodcut should open a single-item page
> -large image on one side
> -full product text on other side - description, price, sizes/stock when I have them. Clicking a card on Products should take someone there.
>
> I need a chat interface on the bottom right. It doesn't have to talk to the agent yet. It is a stub that will call the backend later.
>
> I am going to need a small API to read the db. make a simple fastapi app in backend/main.py to give the products and images. i'll grow it to an agent backend in Prob 5
>
> Since i am working on this new computer, i may not have all the proper front/backedn stuff set up w/ render and github. lmk if i need to troubleshoot that

**Follow-up prompts:**

1. About Us text:

   > Here is some About Us text. I don't see anything like that on the real website?
   >
   > Campus Customs is your New Haven source for officially licensed Yale apparel. Find everything you need online or step into our storefront at 57 Broadway.
   >
   > We are your one-stop shop for any Yale gear you could need: residential colleges, graduate schools, Yale Bulldogs athletics, and, of course, The Game. Whether you're a student, parent, or just want to rep Yale, you'll find what you need here.
   >
   > Have a question about a product, a size, or what's in stock? Chat with us online!

   **What was lacking:** The first prompt asked for the pages in my own voice, but Claude drafted the About Us text itself, so I wrote my own.

2. Home page layout:

   > Home page:
   >
   > Shop Bulldog Blue
   >
   > I like having an all products thing, but above it, let's put a rotating selection of our highest selling items
   >
   > Let's do collections below. Let me know if there's a better way to organize, but i suggest(improve wording)
   > -general yale
   > -residential colleges
   > -graduate and professional schools
   > -Yale Athletics

   **What was lacking:** The first prompt only said the Home page wording should come from the real site, without describing what the page should contain, so this laid out the heading, the rotating product row and the collections.

3. Moving collections into the database:

   > Cool, we can work collections/featured into the database. I don't want it to say "Featured" at the top.

   **What was lacking:** The first version kept collections and featured items only in the code and put a "Featured" heading over the carousel, so I asked to store them in the database and drop the heading.

## Problem 4: Create account and login

**Prompt (my own words):**

> Problem 4: Create account and login
>
> I need a normal account creation/login flow.
>
> For create account, they need to provide first, last, email, and password. they need to confirm the password
>
> for log-in, they need an email and password
>
> new accounts go into the users table. the passwords need to be stored SECURELY so that no hackers can access them. what does this involve, hashing?
>
> My seed database has a test user. I won't tell you those credentials so that you don't mess with it. I'll confirm that I can log in as that user and also create a new account
>
> Let me see what you put in output/harness.md - I want to see how authorization works (what is stored for a user and how are passwords protected?)

**Follow-up prompts:**

1. Test account login failed:

   > I couldn't log in with the test account

   > No match found with common settings.
   >
   > Maybe I am not understanding this assignment correctly?

   **What was lacking:** The first prompt assumed the seed accounts' password hashes would just work, but they didn't record how they were made, so we had to identify the settings (PBKDF2-SHA256, 120,000 rounds) before the test user could log in.

2. Password reveal button:

   > i created a new one. it worked. please tweak the site password reveal thing. you have the option to show. however, if you click away, the option is gone. the option should always be there when you are typing in the password box

   **What was lacking:** The first prompt didn't say how the password boxes should behave, so the site relied on the browser's built-in reveal icon, which disappears when you click away.

3. Password reset:

   > yes, test user logged in. nothing else to do? I wonder if I need a password reset thing?

   **What was lacking:** The first prompt didn't cover forgotten or changed passwords. A real reset needs an email service, so we decided to add a logged-in "change password" feature in Problem 9 instead.

## Problem 5: PydanticAI agent backend

**Prompt (my own words, sent in two parts):**

> I need to build the shop's chatbot as a PydanticAI agent behind FastAPI, which is plugged into my front-end chat widget. The API app should be in backend/main.py. This is the file i run with Uvicorn. The agent should be four files next to it, which is the same concept as in HW 3. Here are the files:
> 1) backend/prompts/prompt.md - system prompt. this will grow as we go
> 2) backend/agent.py - this is the agent entry and wiring
> 3) backend/tools.py

> continuing now, from backend/tools.py - these are the tools the agent can call
> -backend/models.py - these are the pydantic/pydanticAI structured types
>
> main.py should expose a chat route so that a message from the website makes the agent reply (and the hw instructions say "and whatever else you need for products/auth"). I need the AI model API key for the agent. I think I need to paste that in env?
>
> I need Campus Customs "voice and safety basics" to be in prompts/prompt.md. I don't understand this, but it says "Start or update types in models.py for chat replies/product cards as needed.
>
> Output/harness.md should note how the front end communicates with FastAPI and how the agent is loaded.
>
> The backend must run from the backend/ folder like so:
>
> uvicorn main:app --reload --port 8000

**Follow-up prompt:** None needed.

## Problem 6: Tools: product info and stock

**Prompt (my own words):**

> The agent needs tools that can look up real info from the database.
>
> -product description
> -how many are in stock, by size (when the customer asks about it)
> -the price
>
> the agent must use the database and NEVER invent prices or quantities. If a size goes out of stock, it needs to say that clearly.
>
> prompts/prompt.md needs to be expanded so that the agent knows to call those tools for the price and stock questions. I am told to "add or update return types in models.py" - what does that mean?
>
> in the harness markdown doc, i need to list each tool and explain which model fields I chose for lookup results and why i did. let me review your work on this please

**Follow-up prompt:**

> wait, can you give me whatever i need to review for problem 6?

**What was lacking:** The first prompt asked to review the work but didn't say what to include, so Claude pasted the whole harness file; the follow-up narrowed it to just the Problem 6 pieces (requirement checklist, prompt changes, return types and the harness tools section).

## Problem 7: Chat search that updates the page

**Prompt (my own words):**

> Problem 7: Chat search that updates the page
>
> I want my customers to get what they want. When they express interest, I want the item to be available for them. That brings them down the sales funnel. when someone asks about a type of item, the agent shouldn't just give them info, it should also dynamically show those matching items as product cards. i want them to have image, name, price, and short info.
>
> This is a contract w/ the API. The agent will return structured product matches. The frontend renders them on the website.
>
> Once the dynamic product cards get loaded by this new feature, the same single-item page behavior that was built in Problem 3 should work perfectly. each rpodcut card (including these dhyanmic ones), should still open the detail view - large image + full info - when it gets clicked.
>
> Make sure that prompts/prompt.md and harness.md are updated to show clearly how search results reach the page.

**Follow-up prompts:**

1. Choosing where the cards appear:

   > let's try it with both. give me something to prompt the chatbot with

   > I want to do a/b testing with either/or. give me something to prompt the chatbot with

   **What was lacking:** The first prompt didn't say where on the website the cards should appear (inside the chat or on the page), so I asked for both placements behind an A/B switch so I could compare them.

2. Picking the winner:

   > I think I like in chat better. I think it is annoying to have the page changed on you. instead, i think it should show a best match with a "show more" option that will THEN navigate teh page to one with more options

   **What was lacking:** Neither variant matched what I wanted after testing: the chat should show one best match, and the page should only change when the shopper asks to see more.

3. Making the button sell:

   > It should be more appealing than "show all 2 matches"
   >
   > how about something more along the lines of "See more X products" - use your sales brain

   **What was lacking:** My "show more" request didn't specify the button's wording, and "Show all 2 matches" sounded like a search engine instead of a store, so the button now names the products ("See 7 more hoodies").

4. Whole collections:

   > yes, great addition

   (Approving Claude's suggestion that broad questions like "what residential college stuff do you have?" should link to the whole collection, e.g. "Shop all 19 in Residential Colleges", since chat results stop at 8.)

   **What was lacking:** The earlier design capped chat results at 8, so a shopper asking about a big collection only saw part of it.

5. Minimizing the chat:

   > I want the opportunity to minimize the chat. When I navigate to a idfferent page it should auto-memorize

   **What was lacking:** Opening a product from the chat left the chat panel covering the new page, so the chat now minimizes itself on every page change (and can be minimized by hand) while keeping the conversation.

## Problem 8: Customer memory

**Prompt (my own words):**

> I want my shoppers to have their chat histories saved. The agent needs to know who it is chatting with if they're logged in. It needs to know their name and email. That should be in "agent deps" (whatever that is) and/or the tools the agent can call.
>
> There needs to be page context passed to the agent. the example the problem gives is if someone is on a product page and asks "do you have this in pink?" the agent will know what product they mena. This code cna be put into the agent context.
>
> Guests can chat. history only needs to persist for logged-in users.
>
> Put in harness.md how the user chat history gets stored, what customer fields are seen by the agent, and how the page context gets passed.
>
> I imagine that you need some legal disclaimers for storing this data in real life, especially in europe, but this is a class exercise.

**Follow-up prompt** (added later, while working on Problem 10):

> ah, this is actually a backend improvement, so we can write it to problem 8. could we let people click in and see their account? Theoretically it would show past orders and such.

**What was lacking:** The first prompt saved the shopper's data but gave them no place to see it. The follow-up added a My Account page (profile, saved chat, change password). Since the database has no orders, the orders section truthfully says "There are no orders on this account" instead of showing made-up orders.

> For orders, you could just say that there have been no orders in this account. nobody will make an order, so it will be accurate!

## Problem 9: Usability improvements

**Prompt (my own words):**

> Problem 9: Usability improvements
>
> Now, I need to make 2 front-end usability improvements and 2 agent/backend usability improvements.
>
> Before you give suggestions, can you tell me what I've already suggested? I think I have been doing some things beyond the scope of the project.
>
> I'll eventually need a output/usability.md that tells what I added and why it helps a shopper or the business. Wait to write to it. My first thing is to look at what I've already suggested.

**Follow-up prompts:**

1. Noticing the chat was slow:

   > why does it take *so* long to do the chat? Is that something I could improve?

   **What was lacking:** The first prompt didn't name any problems to fix yet; clicking around the site showed me the chat's slowness was the biggest usability issue.

2. Choosing the speed fixes:

   > I think A would be good. Let's try out B. I'm not enthusiastic about it, but it's fine. I don't understand why the prices wouldn't still be called from the database.

   **What was lacking:** I needed to pick which of the suggested fixes to build, and to understand that including prices in search results still reads them from the database.

3. Pushing for real speed:

   > this is barely faster on the chatbot. Can you give me a breakdown of what's taking so long?

   > why are real store chatbots so much faster? they're not using the azure thing?

   > Yeah, let's try that

   **What was lacking:** The first speed fix barely helped, so I asked for measurements of where the time goes, which showed the fixed cost per model call was the bottleneck and led to pre-search and the instant product card.

4. Never making things up:

   > I just don't want to make up anything. that is a HUGE rule here.

   **What was lacking:** The speed changes had the bot answer from data handed to it, so I asked for an audit; it found the bot generalizing from partial search results, which a new honesty rule fixed.

5. Exact whole-catalogue answers:

   > yes!! I think that's a great idea. then it is python doing the database, not the bot.
   >
   > We need to make sure the catalogue gets updated regularly though, right?

   **What was lacking:** After the honesty fix, the bot declined questions like "what's your cheapest item?", so I approved a catalogue summary tool and checked that its totals always come from the live database.

6. Picking the fourth improvement and writing it up:

   > I think A is best. Let's do that. Now, give me some usability text to review

   > Rewrite in "I" - mention that about #2s origin. Length is right

   **What was lacking:** I still needed a second front-end improvement (I chose the chat minimize feature from Problem 7), and the first draft of usability.md wasn't in my voice and didn't explain that feature's origin.

## Problem 10: Style the website

**Prompt (my own words):**

> Problem 10: Style the website.
>
> Oh boy. Let's do all this as if Campus Customs has an *official* partnership with Yale to use fonts, colors, logos, etc.

**Follow-up prompts:**

1. Fonts:

   > Ok, let's do a font that's a look-alike of Yale's

   > Let's use Mallory (or a look alike) actually. not crazy about this for a site

   **What was lacking:** The first prompt didn't pick a font; the Yale-typeface look-alike (a serif) felt too bookish for a website, so I switched to a Mallory look-alike.

2. Campus photos:

   > This site is so boring right now. Can we add campus imagery in a way that doesn't overpower the site?

   > don't like that broadway pic on the about us. it can just be a gorgeous campsu picture

   > something about this page isn't happy enough. we need more happy hale people

   **What was lacking:** The first styling pass had no imagery, then only buildings; I asked for campus photos, then happier photos with people in them.

3. Navigation, logo and colors:

   > For products, you should be able to hover and then see categories or something

   > yeah, add the accent folders

   > Make the banner at the top more interesting. Can we have a yale bulldog for the little icon on the tab?

   > This is a yale project! use the athletics bulldgo! you have my permission

   > wherever it says yale licensed apparel, it should make clear that it's officially licensed

   **What was lacking:** The first prompt didn't cover navigation, accent colors or the logo. The licensing rules turned out to matter: Yale's guide forbids other Ivy schools' colors, so the accents stay blue, and the bulldog marks are only available to licensees, so I chose the official Athletics Block Y.

4. Design goals and spirit:

   > My goal is for this to feel 1) yale 2) exciting/vibrant and 3) school spirity

   > Do those please

   **What was lacking:** I hadn't stated my design goals; once I did, the shopping pages got campus headers, spirited headings and a livelier product page.

5. Stock wording:

   > oh god. don't show how many are in stock. if it is a limited quantity, say the stock. something like "only 4 left"

   > yes, follow that

   **What was lacking:** Showing every count made the store look like a warehouse; now both the site and the chatbot say "In stock", "Only N left" (5 or fewer) or "Out of stock".

## Problem 11: Site testing (app check)

**Prompt (my own words):**

> Problem 11: Site testing (app check)
>
> I need to test the live site and document it in output/app_check.html - this is a page that I can double click open - it needs clear screenshots and short captions for these activities:
>
> -the chat checking the inventory level of an item, giving the honest stock/price from the database (remember, for sales reasons, we need to push for this if it's more than 5)
> -dynamic-search result cards appear after a category question
> -one of my usability features from problem 9. which is best?
>
> the html guide should be easy to grade. it will have a heading for each check, it will have the screenshot, and one or two sentences about what the screenshot proves. The screenshot image files should be in output/app_check_images/ and linked from app_check.html with relative paths (an example is app_check_images/inventory.png)

**Follow-up prompt:** None needed.

## Problem 12: Audit trail, safety, finish harness

**Prompt (my own words):**

> Problem 12: Audit trail, safety, finish harness
>
> I need an append-only output/audit_trail.json for the agent-loop activity. I need to record the time, tool name, short args/result, and the stop reason. it should not be wiped between runs.
>
> I need some safety rules for the agent too. they'll be in the prompt.md doc
>
> I'm thinking...
> -never make up stock
> -never make up prices. you can't be tricked.
> -what else? is there anything it could do that would burn a ton of tokens?
>
> harness.md needs to be totally clear about how this system works. It needs:
> -model fields in models.py and why they were chosen
> -the tools and abilities
> -the safety rules
> -the specs (loop limits, result caps, models, and how to run front + back)

**Follow-up prompt:**

> excellent! yes, tihgtne the rule. then, we can move on to problem 13

*What was lacking:* in testing, the bot listed a quarter-zip's sizes correctly but forgot to say "only 2 left" for two low sizes, so I had it tighten the rule (now also checked in code).

## Problem 13: Push to GitHub and submit the URL

**Prompt (my own words):**

> unzip it. I need to keep these data files locally. i am not supposed to push them to github. I should have a local only data pack with this structure:
>
> data/
> -campus_customs.db
> -products/ #images referenced by the catalogue
>
> my submission will be like such:
> hw4/
> -AI_prompts.md
> -requirements.txt
> -.env.example
> -.gitignore
> -README.md
> NEXT FOLDER
> -frontend/   #Vite React TypeScript app
> NEXT FOLDER
> -backend/ (subfolders)
> -main.py # FastAPI app - run with: uvicorn main:app --reload --port 8000
> -agent.py
> -models.py
> -tools.py
> -prompts/ (subfolder)
> -prompt.md
> BACK UP TO BACKEND/
> -output/ (subfolders)
> -harness.md
> -design.md
> -usability.md
> -app_check.html
> -app_check_images/ (subfolder) #screenshots linked from app_check.html
> -audit_trail.json

**Follow-up prompt:**

> the hw4 folder is going to be pushed to a public GitHub repository and I am going to submit the repo URL. In the past, I've uploaded zips for homeworks, but not this time.
>
> The real .env, campus_customs.db or product images should NOT be in the GitHub repo. I'll use .gitignore. .env.example will have placeholders only
>
> the agent is the four files under backend: prompts/prompt.md, agent.py, tools.py, and models.py
>
> README.md will need to explain how to run the front end and back end after the data pack is placed.

**What the first prompt lacked:** It laid out the folder structure and said the data stays local, but it didn't say the repo would be public and submitted as a URL. It also didn't say how `.env` and `.env.example` should be handled or what the README needs to cover.
