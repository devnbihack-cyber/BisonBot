import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class Rasa {
  private rasaUrl = 'http://localhost:5005/webhooks/rest/webhook';
  constructor(private http: HttpClient) {}
  sendMessage(message: string, sender: string = 'user'): Observable<any> {
    const payLoad = {
      sender: sender,
      message: message,
    };
    return this.http.post(this.rasaUrl, payLoad);
  }
}
