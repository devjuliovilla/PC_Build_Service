import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private http = inject(HttpClient);
  readonly baseUrl = 'http://localhost:8000';

  get<T>(path: string) {
    return this.http.get<T>(`${this.baseUrl}${path}`);
  }

  post<T>(path: string, body?: unknown) {
    return this.http.post<T>(`${this.baseUrl}${path}`, body);
  }

  put<T>(path: string, body?: unknown) {
    return this.http.put<T>(`${this.baseUrl}${path}`, body);
  }

  delete(path: string) {
    return this.http.delete(`${this.baseUrl}${path}`);
  }
}
