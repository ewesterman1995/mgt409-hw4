# Usability Improvements

Four improvements beyond the base requirements: two on the front end and two in the agent and backend. For each, I describe what I added, why it helps shoppers or the business, and how to see it in the running app.

## Front end

### 1. Live progress and an instant product card in the chat

**What I added:** While the chatbot works, the waiting bubble shows what it's actually doing, such as "Found matching products. Writing your answer…", with a pulsing dot, instead of a generic "Typing…". When a message names a product, that product's card (photo, name, price, short description) appears under the progress message right away, about 0.1 seconds after sending, before the written answer arrives.

**Why it helps:** Every reply has to go through the course's AI model, which takes 1.5–2.5 seconds no matter what I do. A blank wait feels longer and makes shoppers wonder if the chat is broken. Showing real progress makes the wait feel shorter and builds trust that the answer comes from the store's actual inventory. The instant card lets the shopper see and click the product before the answer is even written, which keeps them moving toward a purchase.

**How to see it:** Open the chat and ask "Is the Champion Reverse Weave Crewneck in stock in a medium?" The product card appears almost immediately under "Found matching products. Writing your answer…", followed by the answer ("12 left in size M").

### 2. Chat that minimizes itself and keeps the conversation

**What I added:** The chat has a minimize button (–). It also minimizes automatically whenever the shopper goes to another page, for example by clicking a product card in the chat, a "See 7 more hoodies →" button or the nav. The conversation is kept: the minimized button changes from "Chat" to "Continue chat", and reopening shows everything, including product cards. For guests it survives a page refresh; for logged-in shoppers it's saved to their account.

**Where it came from:** I noticed the problem myself while testing the chat in Problem 7. Problem 7 only required that product cards from the chat open the product's detail page. When I clicked one, the detail page opened with the chat panel still covering part of it, so I added minimizing and auto-minimizing on top of what the problem asked for.

**Why it helps:** Without this, the shopper had to close the chat to see the product they just asked about, and closing it felt like losing the conversation. Now the page they chose is always fully visible, and "Continue chat" shows they can pick up where they left off. That keeps shoppers browsing and chatting instead of starting over.

**How to see it:** Ask the chat "I need something for my dad" and click the product card. The product page opens, the chat collapses to "Continue chat", and clicking it shows the full conversation.

## Agent and backend

### 3. Faster answers

**What I added:** I measured where reply time goes. Every call to the course model costs about 1.3 seconds of fixed overhead, while my database lookups take 3 milliseconds, so the only real speed lever was making fewer model calls. I made three changes:

- **Pre-search:** before calling the model, the backend searches the database for the product the message is clearly about, or the product page the shopper is on, and gives the model those results with live price and stock. It only uses confident matches; vague questions are searched normally.
- **Richer search results:** product search returns the price and stock per size, so price and stock questions don't need a second lookup.
- **JSON-mode answers:** the agent returns its structured reply directly instead of through an extra tool call, which removed a wasted model call on every question.

All prices and stock still come only from the database.

**Why it helps:** Shoppers leave chats that feel slow. Product questions went from three model calls to one:

| Question (measured with caching off) | Before | After |
|---|---|---|
| "How much is the Big Yale hoodie?" | ~3.5 s | 1.7 s |
| "Is the Baseball Left Chest Crewneck in XS?" | 4.2 s | 1.8 s |
| "Show me your hoodies" | 4.4 s | 2.5 s |
| "Where is your store?" | 2.9 s | 1.5 s |

After the change I re-checked 16 answers against the database. Every price, stock count and sold-out size matched.

**How to see it:** Ask a price or stock question about a named product; the answer arrives in about 2 seconds. (Asking the exact same question twice is even faster, because the course's AI gateway caches repeated requests.)

### 4. Exact answers about the whole catalogue

**What I added:** A new agent tool, `catalogue_summary`, that has Python count the entire catalogue with database queries every time it's called: how many products there are overall and of each kind (hoodies, T-shirts, quarter-zips…), how many are in stock, price ranges, and the cheapest and most expensive items. The model only reads the results.

**Why it helps:** Product search shows the bot at most 8 items. Before this tool, questions like "What's your cheapest item?" made the bot either guess from those 8 (risking a made-up answer, which breaks my rule never to invent store data) or decline unhelpfully. Now shoppers get exact, trustworthy answers to common comparison questions. Because the totals are recalculated from the live database every time, they're always current; there's no copy to update.

**How to see it:** Ask "What's the cheapest thing you sell?" (answer: $32.00, shared by 25 T-shirts) or "How many hoodies do you have?" (27, all in stock). Both match the database.
