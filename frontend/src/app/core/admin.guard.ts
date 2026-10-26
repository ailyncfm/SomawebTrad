import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { map, catchError, of } from 'rxjs';
import { AuthService } from './auth.service';

export const adminGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);

  const checkAdmin = (): boolean => {
    if (auth.isAdmin()) return true;
    router.navigate(['/']);
    return false;
  };

  if (auth.user() !== null) {
    return checkAdmin();
  }

  return auth.me().pipe(
    map(() => checkAdmin()),
    catchError(() => {
      router.navigate(['/login']);
      return of(false);
    })
  );
};