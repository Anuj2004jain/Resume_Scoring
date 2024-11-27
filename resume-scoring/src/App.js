import React, { useState } from "react";
import axios from "axios";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";
import { Bar } from "react-chartjs-2";

// Register required Chart.js components
ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

function App() {
  const [file, setFile] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [error, setError] = useState("");

  const handleFileChange = (event) => {
    setFile(event.target.files[0]);
    setError("");
    setAnalysis(null);
  };

  const handleDownload = async () => {
    if (!analysis) {
      setError("Please analyze a resume before downloading the report.");
      return;
    }

    try {
      const response = await axios.post(
        "http://127.0.0.1:5000/download",
        analysis,
        {
          responseType: "blob",
        }
      );

      const blob = new Blob([response.data], { type: "application/pdf" });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "resume_analysis_report.pdf";
      link.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError("Failed to download the report.");
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError("Please upload a file.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await axios.post(
        "http://127.0.0.1:5000/analyze",
        formData,
        {
          headers: { "Content-Type": "multipart/form-data" },
        }
      );
      setAnalysis(response.data);
    } catch (err) {
      setError(err.response?.data?.error || "An error occurred.");
    }
  };

  const chartData = {
    labels: ["Relevance", "Formatting", "Overall Score"],
    datasets: [
      {
        label: "Resume Scores",
        data: [
          analysis?.relevance_score || 0,
          analysis?.formatting_score || 0,
          analysis?.score || 0,
        ],
        backgroundColor: ["#4CAF50", "#2196F3", "#FFC107"],
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: { display: true },
      title: { display: true, text: "Resume Analysis Scores" },
    },
  };

  return (
    <div class="min-h-screen bg-gradient-to-r from-gray-50 via-gray-100 to-gray-50 flex items-center justify-center">
  <div class="w-full max-w-4xl bg-white shadow-xl rounded-lg p-8 border-t-4 border-blue-500">
    <h1 class="text-3xl font-bold text-gray-700 text-center mb-6">Resume Scoring Application</h1>

        <div className="file-upload border-2 border-dashed border-gray-400 rounded-lg p-6 text-center hover:bg-gray-50 transition mb-6">
          <input
            type="file"
            onChange={handleFileChange}
            accept=".pdf"
            className="mb-4"
          />
          <button
            onClick={handleUpload}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition"
          >
            Upload
          </button>
        </div>

        {error && <p className="text-red-500 text-center mb-4">{error}</p>}

        {analysis && (
          <div className="results bg-gray-50 p-6 rounded-lg border border-gray-300">
            <h2 className="text-xl font-semibold mb-4">
              Resume Analysis Results
            </h2>

            {/* Scores Chart */}
            <div className="max-w-lg mx-auto mb-6">
              <Bar data={chartData} options={chartOptions} />
            </div>

            {/* Detailed Analysis */}
            <div className="details space-y-4">
              <h2 className="text-lg font-semibold">
                Resume Score: {analysis.score}
              </h2>
              <p>
                <strong>Missing Sections:</strong>{" "}
                {analysis.missing_sections?.join(", ") || "None"}
              </p>
              <p>
                <strong>Scoring Criteria:</strong> {analysis.scoring_criteria}
              </p>

              <div>
                <h3 className="font-semibold">Strengths:</h3>
                <ul className="list-disc pl-5">
                  {analysis.strengths
                    .split(/\*\s+/)
                    .filter((strength) => strength.trim() !== "")
                    .map((strength, index) => {
                      const parts = strength.replace(/\*/g, "").trim().split(":"); // Split at ":" to identify parts
                      const boldPart = parts[0].trim(); // Text before ":"
                      const remainingPart = parts.slice(1).join(":").trim();
                      return(
                        <div key={index} style={{ marginBottom: "10px" }}>
                        <span style={{ fontWeight: parts.length > 1 ? "bold" : "normal" }}>
                          {parts.length > 1 ? `${boldPart}:` : strength.trim()}
                        </span>
                        {remainingPart && ` ${remainingPart}`}
                      </div>
                    )})}
                </ul>
              </div>

              <div>
                <h3 className="font-semibold">Weaknesses:</h3>
                <ul className="list-disc pl-5">
                  {analysis.weeknesses
                    .split(/\*\s+/)
                    .filter((weekness) => weekness.trim() !== "")
                    .filter(weekness => weekness.includes('*'))
                    .map((weekness, index) => (
                      <div key={index}>{weekness.replace(/\*/g, "").trim()}</div>
                    ))}
                </ul>
              </div>

              <div>
                <h3 className="font-semibold">Suggestions:</h3>
                <ul className="list-disc pl-5">
                  {analysis.suggestions
                    .split(/(?:\d+\.\s+|\*\s+)/)
                    .filter((suggestion) => suggestion.trim() !== "")
                    .map((suggestion, index) => {
                      const parts = suggestion.replace(/\*/g, "").trim().split(":"); // Split at ":" to identify parts
                      const boldPart = parts[0].trim(); // Text before ":"
                      const remainingPart = parts.slice(1).join(":").trim();
                      return(
                        <div key={index} style={{ marginBottom: "10px" }}>
                        <span style={{ fontWeight: parts.length > 1 ? "bold" : "normal" }}>
                          {parts.length > 1 ? `${boldPart}:` : suggestion.trim()}
                        </span>
                        {remainingPart && ` ${remainingPart}`}
                      </div>
                      )})}
                </ul>
              </div>
            </div>

            <button
              onClick={handleDownload}
              className="mt-4 bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 transition"
            >
              Download Report
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
