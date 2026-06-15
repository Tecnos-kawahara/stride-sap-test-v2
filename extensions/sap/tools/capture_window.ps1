# capture_window.ps1 - Capture a specific window by title keyword (optionally filtered by PID)
# Usage: powershell -File capture_window.ps1 -Keyword "SAP" -OutFile "screenshot.png" [-FilterPid 12345]

param(
    [string]$Keyword = "SAP",
    [string]$OutFile = "screenshot.png",
    [uint32]$FilterPid = 0
)

Add-Type -AssemblyName System.Drawing

Add-Type @"
using System;
using System.Runtime.InteropServices;
using System.Drawing;
using System.Drawing.Imaging;
using System.Text;

public class WindowCapture {
    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

    [DllImport("user32.dll")] public static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);
    [DllImport("user32.dll")] public static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);
    [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hWnd, out RECT rect);
    [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr hWnd, IntPtr hDC, uint nFlags);
    [DllImport("user32.dll")] public static extern int GetWindowTextLength(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint lpdwProcessId);
    [DllImport("dwmapi.dll")] public static extern int DwmGetWindowAttribute(IntPtr hWnd, int dwAttribute, out RECT pvAttribute, int cbAttribute);
    [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();

    [StructLayout(LayoutKind.Sequential)]
    public struct RECT { public int Left, Top, Right, Bottom; }

    private static IntPtr foundHwnd = IntPtr.Zero;
    private static int foundArea = 0;

    public static IntPtr FindWindow(string keyword, uint filterPid) {
        foundHwnd = IntPtr.Zero;
        foundArea = 0;
        EnumWindows(delegate(IntPtr hWnd, IntPtr lParam) {
            if (!IsWindowVisible(hWnd)) return true;
            if (filterPid != 0) {
                uint wndPid; GetWindowThreadProcessId(hWnd, out wndPid);
                if (wndPid != filterPid) return true;
            }
            int len = GetWindowTextLength(hWnd);
            if (len == 0) return true;
            var sb = new StringBuilder(len + 1);
            GetWindowText(hWnd, sb, sb.Capacity);
            if (sb.ToString().IndexOf(keyword, StringComparison.OrdinalIgnoreCase) >= 0) {
                // When PID filter is active, pick the largest window
                RECT r;
                GetWindowRect(hWnd, out r);
                int area = (r.Right - r.Left) * (r.Bottom - r.Top);
                if (filterPid != 0) {
                    if (area > foundArea) {
                        foundHwnd = hWnd;
                        foundArea = area;
                    }
                    return true; // continue to find largest
                } else {
                    foundHwnd = hWnd;
                    return false; // first match
                }
            }
            return true;
        }, IntPtr.Zero);
        return foundHwnd;
    }

    public static void EnsureDpiAware() {
        SetProcessDPIAware();
    }

    public static bool Capture(IntPtr hWnd, string filePath) {
        // Use DWM extended frame bounds for accurate size
        RECT r;
        int hr = DwmGetWindowAttribute(hWnd, 9, out r, Marshal.SizeOf(typeof(RECT)));
        if (hr != 0) GetWindowRect(hWnd, out r);

        int w = r.Right - r.Left;
        int h = r.Bottom - r.Top;
        if (w <= 0 || h <= 0) return false;

        var bmp = new Bitmap(w, h, PixelFormat.Format32bppArgb);
        var g = Graphics.FromImage(bmp);
        var hdc = g.GetHdc();
        // PW_RENDERFULLCONTENT = 2 (captures even if window is behind others)
        bool ok = PrintWindow(hWnd, hdc, 2);
        g.ReleaseHdc(hdc);

        if (!ok) {
            // Fallback: CopyFromScreen using window position
            g = Graphics.FromImage(bmp);
            g.CopyFromScreen(r.Left, r.Top, 0, 0, new Size(w, h));
        }

        bmp.Save(filePath, ImageFormat.Png);
        g.Dispose();
        bmp.Dispose();
        return true;
    }
}
"@ -ReferencedAssemblies System.Drawing

[WindowCapture]::EnsureDpiAware()
$hwnd = [WindowCapture]::FindWindow($Keyword, $FilterPid)
if ($hwnd -eq [IntPtr]::Zero) {
    Write-Error "Window not found: Keyword='$Keyword' FilterPid=$FilterPid"
    exit 1
}

$result = [WindowCapture]::Capture($hwnd, $OutFile)
if ($result) {
    Write-Host "OK:$OutFile"
} else {
    Write-Error "Capture failed"
    exit 1
}
