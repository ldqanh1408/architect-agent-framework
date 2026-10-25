<#
.SYNOPSIS
    Architect Agent Framework -- multi-harness skill & command installer for Windows PowerShell.
    Supports: claude, codex, dsh, deepseek, opencode, cursor, or all.
#>

[CmdletBinding()]
param(
    [string[]] $Skill = @(),
    [string[]] $Cluster = @(),
    [switch]   $All,
    [ValidateSet('claude', 'codex', 'dsh', 'deepseek', 'opencode', 'cursor', 'all')]
    [string]   $Agent = 'claude',
    [switch]   $Project,
    [string]   $Dest,
    [switch]   $List,
    [switch]   $ListClusters,
    [switch]   $DryRun,
    [switch]   $Force,
    [switch]   $Uninstall
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$ScriptDir        = Split-Path -Parent $MyInvocation.MyCommand.Path
$CatalogRoot      = Join-Path $ScriptDir 'exported_skills'
$PluginCandidate  = Join-Path $ScriptDir 'plugins\architect-agent-framework'
$PluginRoot       = if (Test-Path -LiteralPath $PluginCandidate -PathType Container) { $PluginCandidate } else { $ScriptDir }
$PluginSkillsRoot = Join-Path $PluginRoot 'skills'
$CommandsRoot     = Join-Path $PluginRoot 'commands'
$Marker           = '.architect-agent-framework'

if (-not (Test-Path -LiteralPath $CatalogRoot -PathType Container) -and -not (Test-Path -LiteralPath $PluginSkillsRoot -PathType Container)) {
    throw "Neither catalog ($CatalogRoot) nor plugin skills ($PluginSkillsRoot) found."
}

function Get-Catalog {
    $items = [System.Collections.Generic.List[object]]::new()
    $seenIds = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
    if (Test-Path -LiteralPath $PluginSkillsRoot -PathType Container) {
        Get-ChildItem -LiteralPath $PluginSkillsRoot -Directory | Sort-Object Name | ForEach-Object {
            $sdir = $_.FullName
            $sname = $_.Name
            $smd = Join-Path $sdir 'SKILL.md'
            if (Test-Path -LiteralPath $smd) {
                [void]$seenIds.Add($sname)
                $desc = ''
                $line = Select-String -LiteralPath $smd -Pattern '^description:\s*(.+)$' | Select-Object -First 1
                if ($line) { $desc = $line.Matches[0].Groups[1].Value.Trim().Trim('"') }
                $items.Add([pscustomobject]@{
                    Id          = $sname
                    Kind        = 'foundation'
                    Slug        = 'foundation-sdd'
                    Source      = $sdir
                    Description = $desc
                })
            }
        }
    }
    if (Test-Path -LiteralPath $CatalogRoot -PathType Container) {
    Get-ChildItem -LiteralPath $CatalogRoot -Recurse -File -Filter 'SKILL.md' |
        Sort-Object FullName |
        ForEach-Object {
            $source = $_.Directory
            $rel    = $source.FullName.Substring($CatalogRoot.Length).TrimStart('\', '/')
            $parts  = $rel -split '[\\/]'
            $kind   = switch ($parts[0]) {
                'domains' { 'domain' }
                'tasks'   { 'task' }
                default   { 'orchestration' }
            }
            $slug = if ($parts.Count -ge 3) {
                ("$kind-$($parts[1])" -replace '_', '-').ToLowerInvariant()
            } else {
                $kind
            }
            $description = ''
            $line = Select-String -LiteralPath $_.FullName -Pattern '^description:\s*(.+)$' |
                Select-Object -First 1
            if ($line) { $description = $line.Matches[0].Groups[1].Value.Trim().Trim('"') }

            if ($seenIds.Contains($source.Name)) { return }
            $items.Add([pscustomobject]@{
                Id          = $source.Name
                Kind        = $kind
                Slug        = $slug
                Source      = $source.FullName
                Description = $description
            })
        }
    }
    return $items
}

$Catalog = @(Get-Catalog)
if ($Catalog.Count -eq 0) { throw "No SKILL.md packages found." }

if ($List) {
    $Catalog | ForEach-Object {
        $desc = if ($_.Description.Length -gt 110) { $_.Description.Substring(0, 107) + '...' } else { $_.Description }
        '{0,-42} {1,-40} {2}' -f $_.Id, $_.Slug, $desc
    }
    ''
    "$($Catalog.Count) skills available"
    return
}

if ($ListClusters) {
    $Catalog | Group-Object Slug | Sort-Object Name | ForEach-Object {
        '{0,-46} {1} skills' -f $_.Name, $_.Count
    }
    return
}

if (-not $All -and $Skill.Count -eq 0 -and $Cluster.Count -eq 0) {
    Get-Help $MyInvocation.MyCommand.Path
    throw 'Nothing selected -- pass -Skill, -Cluster, or -All.'
}

$selected = [System.Collections.Generic.List[object]]::new()
if ($All) {
    $Catalog | ForEach-Object { $selected.Add($_) }
}
else {
    foreach ($want in $Skill) {
        $hit = @($Catalog | Where-Object { $_.Id -eq $want })
        if ($hit.Count -eq 0 -and (Test-Path -LiteralPath $CatalogRoot) -and @(Get-ChildItem -LiteralPath $CatalogRoot -Recurse -File -Filter 'skill-contract.yml' |
                Where-Object { $_.Directory.Name -eq $want }).Count -gt 0) {
            throw "'$want' is a skill slot whose content is sold separately -- run: python `"$PluginRoot\scripts\architect_runtime.py`" --bootstrap skills install <downloaded.zip>"
        }
        if ($hit.Count -eq 0) { throw "Unknown skill '$want' -- run -List to see valid ids." }
        $hit | ForEach-Object { $selected.Add($_) }
    }
    foreach ($want in $Cluster) {
        $hit = @($Catalog | Where-Object { $_.Slug -eq $want })
        if ($hit.Count -eq 0) { throw "Unknown cluster '$want' -- run -ListClusters to see valid slugs." }
        $hit | ForEach-Object { $selected.Add($_) }
    }
}
$selected = @($selected | Sort-Object Id -Unique)

function Resolve-Destination {
    param([string] $TargetAgent)
    if ($Dest) { return $Dest }
    $home_ = [Environment]::GetFolderPath('UserProfile')
    $cwd   = (Get-Location).Path
    switch ($TargetAgent) {
        'claude'   { if ($Project) { Join-Path $cwd '.claude\skills' }   else { Join-Path $home_ '.claude\skills' } }
        'codex'    { if ($Project) { Join-Path $cwd '.agents\skills' }   else { Join-Path $home_ '.agents\skills' } }
        'dsh'      { if ($Project) { Join-Path $cwd '.dsh\skills' }      else { Join-Path $home_ '.dsh\skills' } }
        'deepseek' { if ($Project) { Join-Path $cwd '.dsh\skills' }      else { Join-Path $home_ '.dsh\skills' } }
        'opencode' { if ($Project) { Join-Path $cwd '.opencode\skills' } else { Join-Path $home_ '.config\opencode\skills' } }
        'cursor'   { if ($Project) { Join-Path $cwd '.cursor\skills' }   else { Join-Path $home_ '.cursor\skills' } }
        default    { throw "Unknown agent '$TargetAgent'." }
    }
}

function Resolve-CommandDestination {
    param([string] $TargetAgent)
    if ($Dest) { return '' }
    $home_ = [Environment]::GetFolderPath('UserProfile')
    $cwd   = (Get-Location).Path
    switch ($TargetAgent) {
        'claude' { if ($Project) { Join-Path $cwd '.claude\commands' } else { Join-Path $home_ '.claude\commands' } }
        'codex'  { if ($Project) { Join-Path $cwd '.codex\prompts' }   else { Join-Path $home_ '.codex\prompts' } }
        default  { '' }
    }
}

$agents = if ($Agent -eq 'all') { @('claude', 'codex', 'dsh', 'opencode', 'cursor') } else { @($Agent) }

if (-not $DryRun -and -not $Uninstall) {
    try {
        & python (Join-Path $PluginRoot 'scripts\architect_runtime.py') --register-home $ScriptDir | Out-Null
    } catch {}
}

$ok = 0; $skipped = 0; $failed = 0

foreach ($targetAgent in $agents) {
    $destination = Resolve-Destination -TargetAgent $targetAgent
    $action = if ($Uninstall) { 'uninstall' } else { 'install' }
    Write-Host ''
    Write-Host "$action -> $destination" -ForegroundColor Green
    if ($DryRun) { Write-Host '(dry run: no files will be written)' -ForegroundColor DarkGray }

    if (-not $DryRun -and -not $Uninstall) {
        New-Item -ItemType Directory -Path $destination -Force | Out-Null
        $sharedSrc = if (Test-Path -LiteralPath (Join-Path $PluginSkillsRoot '_shared')) { Join-Path $PluginSkillsRoot '_shared' } elseif (Test-Path -LiteralPath (Join-Path $CatalogRoot '_shared')) { Join-Path $CatalogRoot '_shared' } else { '' }
        if ($sharedSrc) {
            $sharedDst = Join-Path $destination '_shared'
            if (Test-Path -LiteralPath $sharedDst) { Remove-Item -LiteralPath $sharedDst -Recurse -Force }
            Copy-Item -LiteralPath $sharedSrc -Destination $sharedDst -Recurse -Force
        }
    }

    foreach ($pkg in $selected) {
        $target = Join-Path $destination $pkg.Id

        if ($Uninstall) {
            if (-not (Test-Path -LiteralPath $target)) { $skipped++; continue }
            if (-not (Test-Path -LiteralPath (Join-Path $target $Marker)) -and -not $Force) {
                Write-Warning "$($pkg.Id): not installed by this script (no $Marker) -- skipped, use -Force to override."
                $skipped++; continue
            }
            if ($DryRun) { Write-Host "  would remove $target" }
            else { Remove-Item -LiteralPath $target -Recurse -Force }
            $ok++
            continue
        }

        if ((Test-Path -LiteralPath $target) -and -not $Force) {
            Write-Host "  skip   $($pkg.Id) (already installed; -Force to overwrite)" -ForegroundColor Yellow
            $skipped++; continue
        }

        if ($DryRun) { Write-Host "  would install $($pkg.Id)"; $ok++; continue }

        try {
            if (Test-Path -LiteralPath $target) { Remove-Item -LiteralPath $target -Recurse -Force }
            Copy-Item -LiteralPath $pkg.Source -Destination $target -Recurse -Force
            Get-ChildItem -LiteralPath $target -Recurse -Directory -Filter '__pycache__' -ErrorAction SilentlyContinue |
                Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
            @(
                'installed-by: architect-agent-framework'
                "skill-id: $($pkg.Id)"
                "cluster: $($pkg.Slug)"
            ) | Set-Content -LiteralPath (Join-Path $target $Marker) -Encoding UTF8
            $ok++
        }
        catch {
            Write-Warning "$($pkg.Id): $($_.Exception.Message)"
            $failed++
        }
    }

    if ($All -and (Test-Path -LiteralPath $CommandsRoot)) {
        $cmdDest = Resolve-CommandDestination -TargetAgent $targetAgent
        if ($cmdDest -and -not $DryRun) {
            if ($Uninstall) {
                Get-ChildItem -LiteralPath $CommandsRoot -File -Filter '*.md' | ForEach-Object {
                    $installedCmd = Join-Path $cmdDest $_.Name
                    if (Test-Path -LiteralPath $installedCmd) { Remove-Item -LiteralPath $installedCmd -Force }
                }
            } else {
                New-Item -ItemType Directory -Path $cmdDest -Force | Out-Null
                Get-ChildItem -LiteralPath $CommandsRoot -File -Filter '*.md' | ForEach-Object {
                    $cmdRaw = (Get-Content -LiteralPath $_.FullName -Raw -Encoding UTF8) -replace '\$\{CLAUDE_PLUGIN_ROOT\}', ($PluginRoot -replace '\\', '/')
                    Set-Content -LiteralPath (Join-Path $cmdDest $_.Name) -Value $cmdRaw -Encoding UTF8 -NoNewline
                }
            }
        }
        if ($targetAgent -in @('dsh', 'deepseek', 'codex') -and -not $DryRun) {
            Get-ChildItem -LiteralPath $CommandsRoot -File -Filter '*.md' | ForEach-Object {
                $cmdId = $_.BaseName
                $cmdTarget = Join-Path $destination $cmdId
                if ($Uninstall) {
                    if (Test-Path -LiteralPath (Join-Path $cmdTarget $Marker)) {
                        Remove-Item -LiteralPath $cmdTarget -Recurse -Force
                    }
                } else {
                    New-Item -ItemType Directory -Path $cmdTarget -Force | Out-Null
                    $raw = Get-Content -LiteralPath $_.FullName -Raw -Encoding UTF8
                    $body = ($raw -replace '(?s)^---\r?\n.*?\r?\n---\r?\n', '') -replace '\$\{CLAUDE_PLUGIN_ROOT\}', ($PluginRoot -replace '\\', '/')
                    $skillContent = "---`nname: $cmdId`ndescription: Execute AAF command /$cmdId`n---`n`n$body"
                    Set-Content -LiteralPath (Join-Path $cmdTarget 'SKILL.md') -Value $skillContent -Encoding UTF8
                    @(
                        'installed-by: architect-agent-framework'
                        "skill-id: $cmdId"
                        'cluster: commands'
                    ) | Set-Content -LiteralPath (Join-Path $cmdTarget $Marker) -Encoding UTF8
                }
            }
        }
    }
}

Write-Host ''
Write-Host "done  ok=$ok skipped=$skipped failed=$failed" -ForegroundColor Green
if (-not $Uninstall -and -not $DryRun -and $ok -gt 0) {
    Write-Host 'Restart your agent so it picks up the new skills and commands.'
}
if ($failed -gt 0) { exit 1 }
