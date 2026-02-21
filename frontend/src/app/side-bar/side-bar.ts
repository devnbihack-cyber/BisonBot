import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MessageShare, ChatSession } from '../services/chat/message-share';

@Component({
  selector: 'app-side-bar',
  imports: [CommonModule],
  templateUrl: './side-bar.html',
  styleUrl: './side-bar.css',
})
export class SideBar {
  isCollapsed = false;
  sessions: ChatSession[] = [];

  constructor(private messageShare: MessageShare) {
    // Subscribe to sessions to display in sidebar
    this.messageShare.sessions$.subscribe((sessions) => {
      this.sessions = sessions;
    });
  }

  toggleSidebar() {
    this.isCollapsed = !this.isCollapsed;
  }

  loadSession(sessionId: string) {
    this.messageShare.loadSession(sessionId);
  }

  getSessions(): ChatSession[] {
    return this.sessions;
  }
}
