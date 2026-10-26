import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { catchError, map, of } from 'rxjs';
import { AuthService } from './auth.service';

export const authGuard: CanActivateFn = (route, state) => {
  const auth = inject(AuthService);
  const router = inject(Router);

  if (auth.isLoggedIn()) return true;

  return auth.me().pipe(
    map(() => true),
    catchError(() => {
      router.navigate(['/login'], { queryParams: { next: state.url } });
      return of(false);
    })
  );
};