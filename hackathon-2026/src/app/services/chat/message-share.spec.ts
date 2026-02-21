import { TestBed } from '@angular/core/testing';

import { MessageShare } from './message-share';

describe('MessageShare', () => {
  let service: MessageShare;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(MessageShare);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
