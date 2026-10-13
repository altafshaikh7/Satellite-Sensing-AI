// Wraps every page with the navbar and the main content area.
import Navbar from "./Navbar.jsx";

export default function PageLayout({ children }) {
  return (
    <div className="app-shell">
      <Navbar />
      <main className="content">{children}</main>
    </div>
  );
}