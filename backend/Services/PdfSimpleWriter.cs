using System.Globalization;
using System.Text;

namespace Backend.Services;

/// <summary>
/// Generador de PDF mínimo, sin librerías externas (para no depender de NuGet
/// mientras el proxy de la VM tenga problemas de certificado). Soporta texto,
/// líneas y saltos de página — suficiente para un documento legible, no
/// pixel-perfect.
/// </summary>
public class PdfSimpleWriter
{
    public const double PageWidth = 595.28;  // A4 en puntos
    public const double PageHeight = 841.89;

    private readonly List<string> _pagesContent = new();
    private StringBuilder _current = new();

    public void NewPage()
    {
        _pagesContent.Add(_current.ToString());
        _current = new StringBuilder();
    }

    private static string Esc(string s)
    {
        var sb = new StringBuilder();
        foreach (var ch in s ?? "")
        {
            if (ch == '(' || ch == ')' || ch == '\\') sb.Append('\\').Append(ch);
            else sb.Append(ch);
        }
        return sb.ToString();
    }

    private static string F(double v) => v.ToString(CultureInfo.InvariantCulture);

    public void Text(double x, double y, string text, double size = 9, bool bold = false)
    {
        var font = bold ? "/F2" : "/F1";
        _current.Append($"BT {font} {F(size)} Tf {F(x)} {F(y)} Td ({Esc(text)}) Tj ET\n");
    }

    public void Line(double x1, double y1, double x2, double y2, double width = 0.5)
    {
        _current.Append($"{F(width)} w {F(x1)} {F(y1)} m {F(x2)} {F(y2)} l S\n");
    }

    public static List<string> WrapText(string text, int maxChars)
    {
        var words = (text ?? "").Split(' ', StringSplitOptions.RemoveEmptyEntries);
        var lines = new List<string>();
        var line = new StringBuilder();
        foreach (var w in words)
        {
            if (line.Length + w.Length + 1 > maxChars && line.Length > 0)
            {
                lines.Add(line.ToString());
                line.Clear();
            }
            if (line.Length > 0) line.Append(' ');
            line.Append(w);
        }
        if (line.Length > 0) lines.Add(line.ToString());
        if (lines.Count == 0) lines.Add("");
        return lines;
    }

    public byte[] Save()
    {
        _pagesContent.Add(_current.ToString());
        _current = new StringBuilder();
        if (_pagesContent.Count == 0) _pagesContent.Add("");

        var pageObjNums = new List<int>();
        var contentObjNums = new List<int>();
        int nextObj = 5;
        foreach (var _ in _pagesContent)
        {
            pageObjNums.Add(nextObj++);
            contentObjNums.Add(nextObj++);
        }

        var sb = new StringBuilder();
        var offsets = new List<int>();

        void WriteObj(int num, string body)
        {
            offsets.Add(sb.Length);
            sb.Append($"{num} 0 obj\n{body}\nendobj\n");
        }

        sb.Append("%PDF-1.4\n");

        int pagesObjNum = 2;
        var kids = string.Join(" ", pageObjNums.Select(n => $"{n} 0 R"));

        WriteObj(1, $"<< /Type /Catalog /Pages {pagesObjNum} 0 R >>");
        WriteObj(2, $"<< /Type /Pages /Kids [{kids}] /Count {pageObjNums.Count} >>");
        WriteObj(3, "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>");
        WriteObj(4, "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>");

        for (int i = 0; i < _pagesContent.Count; i++)
        {
            int pageNum = pageObjNums[i];
            int contentNum = contentObjNums[i];
            WriteObj(pageNum,
                $"<< /Type /Page /Parent {pagesObjNum} 0 R /MediaBox [0 0 {F(PageWidth)} {F(PageHeight)}] " +
                $"/Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> /Contents {contentNum} 0 R >>");

            var content = _pagesContent[i];
            var byteLen = Encoding.GetEncoding("ISO-8859-1").GetByteCount(content);
            WriteObj(contentNum, $"<< /Length {byteLen} >>\nstream\n{content}endstream");
        }

        int xrefStart = sb.Length;
        int totalObjs = 4 + _pagesContent.Count * 2;
        sb.Append($"xref\n0 {totalObjs + 1}\n");
        sb.Append("0000000000 65535 f \n");
        foreach (var off in offsets)
            sb.Append($"{off:D10} 00000 n \n");

        sb.Append("trailer\n");
        sb.Append($"<< /Size {totalObjs + 1} /Root 1 0 R >>\n");
        sb.Append("startxref\n");
        sb.Append(xrefStart);
        sb.Append("\n%%EOF");

        return Encoding.GetEncoding("ISO-8859-1").GetBytes(sb.ToString());
    }
}