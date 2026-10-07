// Lets any part of the site open the chat widget (ChatWidget listens for this event).
export const OPEN_CHAT_EVENT = 'cc:open-chat'

export const openChat = () => window.dispatchEvent(new Event(OPEN_CHAT_EVENT))
