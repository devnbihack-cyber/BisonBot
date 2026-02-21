import { ChangeDetectorRef, Component } from '@angular/core';
import { FormControl, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { Rasa } from '../services/rasa/rasa';
import { MessageShare } from '../services/chat/message-share';

interface Message {
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
}

@Component({
  selector: 'app-chatbox',
  imports: [ReactiveFormsModule, CommonModule],
  templateUrl: './chatbox.html',
  styleUrl: './chatbox.css',
})
export class Chatbox {
  prompt = new FormGroup({
    chat: new FormControl('', [Validators.required]),
  });

  messages: Message[] = [];
  isLoading = false;

  constructor(
    private rasaService: Rasa,
    private cdr: ChangeDetectorRef,
    private messageShare: MessageShare,
  ) {
    // Changed from messages$ to currentMessages$
    this.messageShare.currentMessages$.subscribe((messages) => {
      this.messages = messages;
      this.cdr.detectChanges();
    });
  }

  onSubmit() {
    const userMessage = this.prompt.value.chat?.trim();

    if (!userMessage) {
      return;
    }

    // Add user message to chat
    const userMsg: Message = {
      text: userMessage,
      sender: 'user',
      timestamp: new Date(),
    };

    this.messages = [...this.messages, userMsg];
    this.messageShare.setMessages(this.messages);

    // Clear input
    this.prompt.reset();
    this.isLoading = true;
    this.cdr.detectChanges();

    // Send to Rasa
    this.rasaService.sendMessage(userMessage).subscribe({
      next: (responses) => {
        this.isLoading = false;

        responses.forEach((response: any) => {
          const botMsg: Message = {
            text: response.text,
            sender: 'bot',
            timestamp: new Date(),
          };

          this.messages = [...this.messages, botMsg];
        });

        this.messageShare.setMessages(this.messages);
        this.cdr.detectChanges();
      },

      error: (error) => {
        this.isLoading = false;
        console.error('Error:', error);

        const errorMsg: Message = {
          text: "Sorry, I couldn't connect to the server.",
          sender: 'bot',
          timestamp: new Date(),
        };

        this.messages = [...this.messages, errorMsg];
        this.messageShare.setMessages(this.messages);
        this.cdr.detectChanges();
      },
    });
  }

  startNewChat() {
    this.messageShare.startNewSession();
    this.prompt.reset();
  }
}
