import { NextRequest, NextResponse } from "next/server";
import ExcelJS from "exceljs";
import { isAdmin } from "@/lib/auth";
import { getEvaluationRecords } from "@/lib/dashboard";

export const dynamic = "force-dynamic";

export async function GET(req: NextRequest) {
  if (!(await isAdmin())) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const p = req.nextUrl.searchParams;
  const records = await getEvaluationRecords({
    department: p.get("department") ?? undefined,
    section: p.get("section") ?? undefined,
    language: p.get("language") ?? undefined,
    status: p.get("status") ?? undefined,
  });

  const wb = new ExcelJS.Workbook();
  const ws = wb.addWorksheet("Evaluations");
  ws.columns = [
    { header: "Department", key: "department", width: 18 },
    { header: "Section", key: "section", width: 13 },
    { header: "Language", key: "language", width: 11 },
    { header: "Question ID", key: "question_id", width: 14 },
    { header: "Category", key: "category", width: 20 },
    { header: "Question", key: "question_text", width: 50 },
    { header: "Actual chatbot response", key: "actual_answer", width: 50 },
    { header: "Status", key: "status", width: 16 },
    { header: "Employee comment", key: "comments", width: 40 },
    { header: "Submitted at", key: "submitted_at", width: 20 },
  ];

  for (const r of records) {
    ws.addRow({ ...r, submitted_at: new Date(r.submitted_at) });
  }

  // Brand header: black background, white bold text, yellow bottom border.
  const header = ws.getRow(1);
  header.font = { bold: true, color: { argb: "FFFFFFFF" } };
  header.fill = { type: "pattern", pattern: "solid", fgColor: { argb: "FF111111" } };
  header.eachCell((c) => {
    c.border = { bottom: { style: "medium", color: { argb: "FFF1AB15" } } };
  });
  ws.getColumn("submitted_at").numFmt = "yyyy-mm-dd hh:mm";
  ws.views = [{ state: "frozen", ySplit: 1 }];

  const buffer = await wb.xlsx.writeBuffer();
  return new NextResponse(buffer as ArrayBuffer, {
    headers: {
      "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      "Content-Disposition": 'attachment; filename="chatbot_evaluation_report.xlsx"',
      "Cache-Control": "no-store",
    },
  });
}
