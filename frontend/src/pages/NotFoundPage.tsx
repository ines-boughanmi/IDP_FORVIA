import { Link } from 'react-router-dom';

export function NotFoundPage() {
  return (
    <div className="not-found">
      <h1>Page not found</h1>
      <p>The requested route does not exist in the enterprise frontend.</p>
      <Link className="btn btn-primary" to="/dashboard">
        Return to dashboard
      </Link>
    </div>
  );
}
