param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('worker', 'task')]
    [string]$Kind
)

$ErrorActionPreference = 'Stop'
$secret = [Console]::In.ReadLine()
if ($null -eq $secret -or $secret -notmatch '^[A-Za-z0-9_-]{43,128}$') {
    throw 'A base64url secret of at least 43 characters must be provided on standard input.'
}

$directory = Join-Path $env:LOCALAPPDATA 'SIFederation'
[System.IO.Directory]::CreateDirectory($directory) | Out-Null
$identity = [System.Security.Principal.WindowsIdentity]::GetCurrent().User
$acl = [System.Security.AccessControl.DirectorySecurity]::new()
$acl.SetAccessRuleProtection($true, $false)
$rule = [System.Security.AccessControl.FileSystemAccessRule]::new(
    $identity,
    [System.Security.AccessControl.FileSystemRights]::FullControl,
    [System.Security.AccessControl.InheritanceFlags]::ContainerInherit -bor [System.Security.AccessControl.InheritanceFlags]::ObjectInherit,
    [System.Security.AccessControl.PropagationFlags]::None,
    [System.Security.AccessControl.AccessControlType]::Allow
)
$acl.AddAccessRule($rule)
[System.IO.Directory]::SetAccessControl($directory, $acl)

$targetName = if ($Kind -eq 'worker') { 'worker-token.dpapi' } else { 'task-token.dpapi' }
$target = Join-Path $directory $targetName
$dpapiSource = @'
using System;
using System.ComponentModel;
using System.Runtime.InteropServices;

public static class SiDpapi
{
    [StructLayout(LayoutKind.Sequential)]
    private struct DATA_BLOB { public int cbData; public IntPtr pbData; }

    [DllImport("crypt32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
    private static extern bool CryptProtectData(ref DATA_BLOB input, string description,
        IntPtr entropy, IntPtr reserved, IntPtr prompt, int flags, out DATA_BLOB output);
    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern IntPtr LocalFree(IntPtr memory);

    public static byte[] Protect(byte[] plain)
    {
        GCHandle pin = GCHandle.Alloc(plain, GCHandleType.Pinned);
        try
        {
            DATA_BLOB input = new DATA_BLOB { cbData = plain.Length, pbData = pin.AddrOfPinnedObject() };
            DATA_BLOB output;
            if (!CryptProtectData(ref input, "SI Federation local token", IntPtr.Zero,
                    IntPtr.Zero, IntPtr.Zero, 0, out output))
                throw new Win32Exception(Marshal.GetLastWin32Error());
            try
            {
                byte[] result = new byte[output.cbData];
                Marshal.Copy(output.pbData, result, 0, result.Length);
                return result;
            }
            finally { LocalFree(output.pbData); }
        }
        finally { pin.Free(); }
    }
}
'@
Add-Type -TypeDefinition $dpapiSource -Language CSharp
$bytes = [System.Text.Encoding]::UTF8.GetBytes($secret)
try {
    $protected = [SiDpapi]::Protect($bytes)
    [System.IO.File]::WriteAllBytes($target, $protected)
}
finally {
    [System.Array]::Clear($bytes, 0, $bytes.Length)
    $secret = $null
}
[System.Console]::WriteLine("$Kind secret stored with Windows DPAPI for the current user.")
