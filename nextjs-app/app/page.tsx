import EvaluationApp from "./EvaluationApp";

export default function Home() {
  return (
    <>
      <h1>Chatbot pilot testing</h1>
      <p className="caption">
        Bank of Abyssinia · Internal evaluation platform — select your department and complete
        the assigned testing questions.
      </p>
      <EvaluationApp />
    </>
  );
}
