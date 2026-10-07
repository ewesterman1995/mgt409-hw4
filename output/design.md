# Campus Customs Design

## My design goals

I designed the store as if Campus Customs had an official licensing partnership with Yale. I wanted it to feel:

1. **Yale**: instantly recognizable as Yale's own look, so shoppers trust that the gear is the real thing.
2. **Exciting and vibrant**: lively and full of people, not a plain catalogue.
3. **School-spirited**: game days, graduations, Bulldog pride, the feelings that make someone want to wear Yale.

Every change below serves at least one of these goals and, ultimately, the goal of turning visitors into buyers. Nothing is left from the default Vite styling.

## 1. Feels like Yale

**Official colors, used the way Yale's licensing rules require.** I matched the colors in Yale's licensing brand guide (Yale Brand Guidelines, Yale Licensing 2022): Yale Blue `#00356B` for the header, footer and headings; High Intensity Blue `#286DC0` only for things shoppers can act on (buttons, links, the chat button, selected filters); and Yale Gray for thin borders. The guide forbids putting Yale marks on other Ivy schools' colors (Harvard crimson, Princeton orange, Penn and Cornell red, Dartmouth green), so I kept every accent blue. *Why it sells:* a licensed store that looks exactly like Yale feels trustworthy, and a single bright accent color teaches shoppers at a glance what is clickable.

**Yale's typeface style.** Yale's websites use Mallory, a licensed font I can't put in a public repo, so I used Source Sans 3, a free look-alike with the same open, friendly shapes. I tried a look-alike of the "Yale" serif first, but it felt bookish on a website. *Why it sells:* the font is easy to read at small sizes, which matters most for prices, sizes and the chat.

**The official Yale Athletics Block Y.** The Block Y sits next to the "Campus Customs" wordmark in the header and is the icon on the browser tab, the same mark yalebulldogs.com uses. (The bulldog marks are only given to licensees and the guide says not to redraw them, so I used the Block Y rather than invent a bulldog.) *Why it sells:* it signals "official Yale gear" in the first second, even in a crowded row of browser tabs.

**"Officially licensed" everywhere it counts.** The header, the home banner and the About page say "officially licensed Yale apparel", and the footer carries the legal line Yale requires on licensed products: "The Marks on this product are trademarks of Yale University and are used under official license." *Why it sells:* parents and alumni buying gifts want to know it's authentic.

**Real campus photos.** Harkness Tower, Old Campus, Branford College and the Sterling Law Building appear on the home page, the collection tiles, the Products page header and the About page. They're freely licensed from Wikimedia Commons and credited on a Photo credits page linked from the footer. *Why it sells:* the photos connect each product to a place the shopper loves.

## 2. Exciting and vibrant

**A home banner slideshow full of happy people.** The banner crossfades between Yale cheerleaders at the Yale Bowl, graduates in caps and gowns, and Harkness Tower in fall color, with a slow zoom. A Yale Blue fade on the left keeps "Shop Bulldog Blue" readable, and two buttons (Shop all products, Ask our assistant) give a next step right away. *Why it sells:* people and motion grab attention, and the buttons turn that attention into a click.

**A livelier header.** A thin Yale Blue strip on top ("Officially licensed Yale apparel · 57 Broadway, New Haven · Questions? Chat with us"), then a white bar with the logo, bold navy links and a bright-blue "Create Account" button. It stays pinned while scrolling on desktop. *Why it sells:* shopping and the assistant are always one click away.

**Motion with a purpose.** Product cards lift and outline in bright blue on hover, collection photos zoom slightly, and the Products menu fades in. Everything animated is turned off for shoppers whose device asks for reduced motion. *Why it sells:* hover feedback makes the site feel responsive and invites clicking into products.

**Color breaks up the white.** A light Yale Blue band sits behind the collections, the Products page has a campus-photo header, and the footer is solid Yale Blue. *Why it sells:* the page has rhythm, so the eye keeps moving down toward more products.

## 3. School spirit

**Spirited wording.** "Shop Bulldog Blue" on the banner, "Find Your Corner of Yale" above the collections, "Shop the Bulldog Lineup" on the Products page and "Back to the lineup" on product pages. The banner's line, "For students, parents, and anyone who wants to rep Yale," comes from my own About Us text. *Why it sells:* it talks like a fan, not a warehouse.

**Collections that match how Yale people identify.** The home page tiles (Classic Yale, Residential Colleges, Graduate & Professional Schools, Yale Athletics, Yale Family) each have their own photo: an Old Campus fall scene, a Branford courtyard, Sterling Law, the Bulldogs football team, and graduates. *Why it sells:* a Branford student or a proud parent finds "their" section in one click.

**Game-day and graduation moments.** The cheerleader, football team and graduation photos put the products in the moments people buy them for. *Why it sells:* shoppers picture themselves wearing the gear at The Game or Commencement.

## Shopping pages

**Products menu.** Hovering over "Products" opens a menu with two columns, Collections and Shop by type (Hoodies, T-shirts, Quarter-zips...), each with a live item count. The Products page repeats both as buttons for phones, where hover doesn't exist. *Why it sells:* shoppers reach the right shelf without scrolling through all 102 products.

**Product page.** Each product shows its collection as a clickable badge. Sizes sit in a light-blue panel as bold tiles: "In stock", "Only N left!" (5 or fewer, in bright blue) or "Out of stock" (grayed out and crossed through). Below them, "Questions about this item? Ask our assistant" opens the chat, which already knows which product the shopper is looking at. *Why it sells:* showing exact counts only when stock is low creates honest urgency without making the store look like a warehouse, and help is right where size decisions are made. The chatbot follows the same stock rule.

**Chat interface.** The chat matches the brand: Yale Blue header, bright-blue Chat button and links, product cards in the conversation, and a live progress line while it works. *Why it sells:* it feels like part of the store, not a bolted-on widget, so shoppers trust its answers.

## Accessibility and responsiveness

- Text colors meet contrast guidelines. Yale Gray is too light for small text, so I used it only for borders.
- All motion respects the "reduce motion" setting.
- On phones the header scrolls away instead of covering the screen, the Products menu becomes on-page buttons, and grids collapse to fewer columns.
