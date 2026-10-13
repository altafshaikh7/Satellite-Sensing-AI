// Application root: layout plus the analysis page.
import PageLayout from "./layout/PageLayout.jsx";
import Analyze from "./pages/Analyze.jsx";
import "./index.css";
import "./app.css";

export default function App() {
  return (
    <PageLayout>
      <Analyze />
    </PageLayout>
  );
}