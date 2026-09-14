export default function Home() {
  return (
    <main
      style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        background: "#0D0B14",
        color: "#E8E6F2",
        fontFamily: "Space Grotesk, sans-serif",
      }}
    >
      <h1 style={{ fontSize: 32, fontWeight: 600, color: "#F0A500", marginBottom: 8 }}>
        Eye of Abyss
      </h1>
      <p style={{ color: "#8884A8", fontStyle: "italic" }}>
        &ldquo;And if you gaze long into an abyss, the abyss also gazes back into you.&rdquo;
      </p>
      <p style={{ marginTop: 32, color: "#4A4768", fontSize: 12 }}>
        Dashboard coming — frontend scaffold ready.
      </p>
    </main>
  );
}
