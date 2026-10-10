import { jsPDF } from "jspdf";

export function exportReportToPdf(report) {
  if (!report) return;

  const doc = new jsPDF({
    orientation: "portrait",
    unit: "mm",
    format: "a4",
  });

  const pageWidth = doc.internal.pageSize.getWidth();
  const pageHeight = doc.internal.pageSize.getHeight();
  const margin = 16;
  const contentWidth = pageWidth - margin * 2;
  const footerSpace = 16;
  let y = margin;

  function ensureSpace(requiredHeight = 12) {
    if (y + requiredHeight > pageHeight - footerSpace) {
      doc.addPage();
      y = margin;
    }
  }

  function addWrappedText(text, fontSize = 9.5, isBold = false, color = [40, 50, 70], lineSpacing = 4.5) {
    doc.setFont("helvetica", isBold ? "bold" : "normal");
    doc.setFontSize(fontSize);
    doc.setTextColor(color[0], color[1], color[2]);

    const lines = doc.splitTextToSize(String(text ?? ""), contentWidth);
    const requiredHeight = lines.length * lineSpacing;

    ensureSpace(requiredHeight + 2);
    doc.text(lines, margin, y);
    y += requiredHeight;
  }

  // --- Top Branding Banner ---
  doc.setFillColor(11, 16, 32); // #0B1020 deep midnight navy
  doc.rect(margin, y, contentWidth, 24, "F");

  // Accent cyan line
  doc.setFillColor(66, 217, 248); // #42D9F8 electric cyan
  doc.rect(margin, y + 23, contentWidth, 1.2, "F");

  // Title
  doc.setTextColor(255, 255, 255);
  doc.setFont("helvetica", "bold");
  doc.setFontSize(16);
  doc.text("API SENTINEL", margin + 6, y + 10);

  doc.setFont("helvetica", "normal");
  doc.setFontSize(9);
  doc.setTextColor(150, 180, 220);
  doc.text("API DRIFT DETECTOR & BACKWARD COMPATIBILITY LINTER", margin + 6, y + 16);

  // Status Badge in header
  const isFail = report.result === "FAIL" || (report.summary?.breakingChanges ?? 0) > 0;
  if (isFail) {
    doc.setFillColor(220, 38, 38); // Red
    doc.setTextColor(255, 255, 255);
    doc.roundedRect(pageWidth - margin - 32, y + 5.5, 26, 12, 1.5, 1.5, "F");
    doc.setFont("helvetica", "bold");
    doc.setFontSize(10);
    doc.text("FAIL", pageWidth - margin - 19, y + 13, { align: "center" });
  } else {
    doc.setFillColor(16, 185, 129); // Green
    doc.setTextColor(255, 255, 255);
    doc.roundedRect(pageWidth - margin - 32, y + 5.5, 26, 12, 1.5, 1.5, "F");
    doc.setFont("helvetica", "bold");
    doc.setFontSize(10);
    doc.text("PASS", pageWidth - margin - 19, y + 13, { align: "center" });
  }

  y += 28;

  // --- Metadata Section Box ---
  doc.setFillColor(245, 247, 252);
  doc.roundedRect(margin, y, contentWidth, 22, 2, 2, "F");
  doc.setDrawColor(210, 220, 235);
  doc.roundedRect(margin, y, contentWidth, 22, 2, 2, "S");

  doc.setFontSize(8.5);
  doc.setTextColor(100, 116, 139);
  doc.setFont("helvetica", "bold");
  doc.text("AUDIT METADATA", margin + 4, y + 5.5);

  doc.setFont("helvetica", "normal");
  doc.setTextColor(30, 41, 59);
  doc.text(`Generated: ${new Date().toLocaleString()}`, margin + 4, y + 11);
  doc.text(`Files: ${report.oldFileName} -> ${report.newFileName}`, margin + 4, y + 16.5);

  doc.text(`Version: v${report.oldVersion} -> v${report.newVersion}`, pageWidth / 2 + 10, y + 11);
  doc.text(`Engine: FastAPI Deterministic AST Comparer`, pageWidth / 2 + 10, y + 16.5);

  y += 26;

  // --- Executive Summary Metric Boxes ---
  ensureSpace(22);
  doc.setFont("helvetica", "bold");
  doc.setFontSize(11);
  doc.setTextColor(15, 23, 42);
  doc.text("EXECUTIVE COMPLIANCE SUMMARY", margin, y);
  y += 4;

  const colWidth = (contentWidth - 6) / 3;

  // Box 1: Total Changes
  doc.setFillColor(241, 245, 249);
  doc.roundedRect(margin, y, colWidth, 16, 1.5, 1.5, "F");
  doc.setFontSize(8);
  doc.setTextColor(100, 116, 139);
  doc.text("TOTAL CHANGES", margin + 4, y + 5);
  doc.setFontSize(13);
  doc.setFont("helvetica", "bold");
  doc.setTextColor(15, 23, 42);
  doc.text(String(report.summary?.totalChanges ?? 0), margin + 4, y + 12);

  // Box 2: Breaking Changes
  doc.setFillColor(254, 242, 242);
  doc.roundedRect(margin + colWidth + 3, y, colWidth, 16, 1.5, 1.5, "F");
  doc.setFontSize(8);
  doc.setTextColor(185, 28, 28);
  doc.text("BREAKING CHANGES", margin + colWidth + 7, y + 5);
  doc.setFontSize(13);
  doc.setFont("helvetica", "bold");
  doc.text(String(report.summary?.breakingChanges ?? 0), margin + colWidth + 7, y + 12);

  // Box 3: Warnings
  doc.setFillColor(254, 243, 199);
  doc.roundedRect(margin + (colWidth + 3) * 2, y, colWidth, 16, 1.5, 1.5, "F");
  doc.setFontSize(8);
  doc.setTextColor(180, 83, 9);
  doc.text("WARNINGS", margin + (colWidth + 3) * 2 + 4, y + 5);
  doc.setFontSize(13);
  doc.setFont("helvetica", "bold");
  doc.text(String(report.summary?.warnings ?? 0), margin + (colWidth + 3) * 2 + 4, y + 12);

  y += 22;

  // --- Detailed Findings Section ---
  ensureSpace(14);
  doc.setFont("helvetica", "bold");
  doc.setFontSize(11);
  doc.setTextColor(15, 23, 42);
  doc.text("DETECTED SCHEMA DRIFT FINDINGS", margin, y);
  y += 5;

  const changes = report.changes || [];

  if (changes.length === 0) {
    addWrappedText("No breaking changes or schema drift were detected by the implemented comparison rules.", 9.5, false, [75, 85, 99]);
  } else {
    changes.forEach((finding, index) => {
      ensureSpace(28);

      const isBreaking = finding.type === "BREAKING";
      const isWarn = finding.type === "WARNING";

      // Finding Header Bar
      if (isBreaking) {
        doc.setFillColor(254, 242, 242);
        doc.setDrawColor(252, 165, 165);
      } else if (isWarn) {
        doc.setFillColor(254, 243, 199);
        doc.setDrawColor(253, 230, 138);
      } else {
        doc.setFillColor(240, 249, 255);
        doc.setDrawColor(186, 230, 253);
      }

      doc.roundedRect(margin, y, contentWidth, 7, 1, 1, "FD");

      // Finding # and Title
      doc.setFont("helvetica", "bold");
      doc.setFontSize(9);
      if (isBreaking) doc.setTextColor(185, 28, 28);
      else if (isWarn) doc.setTextColor(180, 83, 9);
      else doc.setTextColor(3, 105, 161);

      doc.text(`[${finding.type}] #${index + 1}: ${finding.title}`, margin + 3, y + 4.8);

      // Risk Tag
      const riskText = `RISK: ${finding.risk || "LOW"}`;
      doc.setFontSize(7.5);
      doc.text(riskText, pageWidth - margin - 3, y + 4.8, { align: "right" });

      y += 9;

      // Details
      addWrappedText(`Location: ${finding.endpoint}`, 8.5, true, [30, 41, 59], 3.8);
      addWrappedText(`Details: ${finding.description}`, 8.5, false, [71, 85, 105], 3.8);

      if (finding.recommendation) {
        addWrappedText(`Remediation: ${finding.recommendation}`, 8.5, false, [15, 118, 110], 3.8);
      }

      y += 2.5;
    });
  }

  // --- Disclaimer ---
  ensureSpace(16);
  y += 4;
  doc.setFont("helvetica", "bold");
  doc.setFontSize(8);
  doc.setTextColor(100, 116, 139);
  doc.text("ENGINE NOTICE & DISCLAIMER", margin, y);
  y += 4;
  doc.setFont("helvetica", "normal");
  addWrappedText(
    "This report reflects the deterministic AST comparison rules executed by API Sentinel against OpenAPI 3.x specifications. " +
    "Verify all reported breaking changes with downstream clients before staging deployment.",
    7.5,
    false,
    [120, 130, 145],
    3.2
  );

  // --- Footers & Page Numbers ---
  const totalPages = doc.internal.getNumberOfPages();
  for (let page = 1; page <= totalPages; page += 1) {
    doc.setPage(page);
    doc.setFontSize(8);
    doc.setTextColor(140, 150, 165);
    doc.setDrawColor(220, 230, 240);
    doc.line(margin, pageHeight - 10, pageWidth - margin, pageHeight - 10);
    doc.text(
      "API Sentinel · Automated Backward Compatibility Linter",
      margin,
      pageHeight - 6
    );
    doc.text(
      `Page ${page} of ${totalPages}`,
      pageWidth - margin,
      pageHeight - 6,
      { align: "right" }
    );
  }

  const safeOldVer = (report.oldVersion || "v1").replace(/[^a-zA-Z0-9._-]/g, "");
  const safeNewVer = (report.newVersion || "v2").replace(/[^a-zA-Z0-9._-]/g, "");
  doc.save(`api-sentinel-audit-${safeOldVer}-to-${safeNewVer}.pdf`);
}

