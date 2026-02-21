import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

export interface ChatSession {
  id: string;
  title: string;
  timestamp: Date;
  messages: any[];
}

@Injectable({
  providedIn: 'root',
})
export class MessageShare {
  firstMessage: string;

  constructor() {
    this.firstMessage = '';
  }
  // List of all chat sessions shown in the sidebar
  sessions: ChatSession[] = [];
  sessions$ = new BehaviorSubject<ChatSession[]>([]);

  // Messages in the current open chat
  currentMessages: any[] = [];
  currentMessages$ = new BehaviorSubject<any[]>([]);

  // ID of the chat we are currently in
  currentSessionId: string = '';

  // Start a brand new empty chat
  startNewSession() {
    this.currentMessages = [];
    this.currentMessages$.next([]);
    this.currentSessionId = Date.now().toString(); // use timestamp as unique id
  }

  // Called every time a new message is added
  setMessages(messages: any[]) {
    // Save messages so we can show them
    this.currentMessages = messages;
    this.currentMessages$.next(messages);

    // Check if this session is already saved in the sidebar
    const alreadySaved = this.sessions.find((s) => s.id === this.currentSessionId);

    if (alreadySaved) {
      // Session exist just update its messages
      alreadySaved.messages = messages;
      alreadySaved.timestamp = new Date();
      this.sessions$.next([...this.sessions]);
    } else {
      // Session is new so add it to the sidebar
      // Find the first message the user sent to use as the title
      const firstUserMessage = messages.find((m) => m.sender === 'user');

      this.firstMessage = firstUserMessage.text;

      if (firstUserMessage) {
        // Trim the title to 40 characters atmost
        let title = firstUserMessage.text;
        if (title.length > 40) {
          title = title.substring(0, 40) + '...';
        }

        // Build the session object
        const newSession: ChatSession = {
          id: this.currentSessionId,
          title: title,
          timestamp: new Date(),
          messages: messages,
        };

        // Add to the top of the list
        this.sessions.unshift(newSession);
        this.sessions$.next([...this.sessions]);
      }
    }
  }

  // Load an old chat when user clicks it in the sidebar
  loadSession(sessionId: string) {
    const session = this.sessions.find((s) => s.id === sessionId);

    if (session) {
      this.currentSessionId = session.id;
      this.currentMessages = session.messages;
      this.currentMessages$.next([...session.messages]);
    }
  }

  // Return all sessions which will be used in side bar
  getSessions(): ChatSession[] {
    return this.sessions;
  }

  getFirstMessage() {
    return this.firstMessage;
  }
}
