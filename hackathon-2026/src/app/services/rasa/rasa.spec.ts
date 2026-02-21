import { TestBed } from '@angular/core/testing';

import { Rasa } from './rasa';

describe('Rasa', () => {
  let service: Rasa;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(Rasa);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
