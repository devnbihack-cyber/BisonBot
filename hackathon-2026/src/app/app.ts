import { Component, signal } from '@angular/core';
import { SideBar } from './side-bar/side-bar';
import { Chatbox } from './chatbox/chatbox';

@Component({
  selector: 'app-root',
  imports: [SideBar, Chatbox],
  templateUrl: './app.html',
  styleUrl: './app.css',
})
export class App {
  protected readonly title = signal('hackathon-2026');
}
