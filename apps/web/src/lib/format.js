// Email se avatar ke initials banata hai: alice.khan@acme.test -> AK
export function initials(email = '') {
  const name = email.split('@')[0] || '';
  const letters = name
    .split(/[._-]/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0].toUpperCase())
    .join('');
  return letters || 'U';
}