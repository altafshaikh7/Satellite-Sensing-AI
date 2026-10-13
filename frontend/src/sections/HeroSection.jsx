// Intro card at the top of the analysis page.
export default function HeroSection() {
  return (
    <section className="hero">
      <h1 className="page-title">SatQuery AI</h1>
      <p>
        Upload satellite images and ask a question. The system validates the inputs,
        selects the appropriate tool, and shows the result on a map with an execution trace.
      </p>
    </section>
  );
}