# Mac Keep-Awake With Amphetamine

This is the preferred Mac keep-awake workflow for local agents, music, transfers, and short attended lid-closed sessions.

Use **Amphetamine** as the GUI/menu-bar control surface. Do not maintain a custom `pmset` supervisor unless Amphetamine fails a concrete local validation case.

## Install

1. Install Amphetamine from the Mac App Store:

   ```bash
   mas get 937984704
   ```

   If the command asks for App Store, sudo, Touch ID, or password interaction, install from the App Store GUI instead. The trusted app is **Amphetamine** by **William Gustafson**.

2. Launch Amphetamine from `/Applications/Amphetamine.app`.

3. On Apple Silicon Mac laptops, install **Power Protect** if Amphetamine prompts for it or if closed-display sessions misbehave when connecting/disconnecting power. Power Protect is the official helper path for Apple Silicon closed-display behavior around power-source changes.

4. Install **Amphetamine Enhancer** only if needed for expanded process/app trigger visibility or if Amphetamine directs you to it. It is not required for the first setup unless closed-display or trigger behavior needs it.

Power Protect's installer should create:

```text
~/Library/Application Scripts/com.if.Amphetamine/powerProtect.scpt
/private/etc/sudoers.d/amphetamine_PowerProtect
```

The sudoers filename is case-sensitive on case-sensitive filesystems; verify the observed local filename after installation. The sudoers rule should be intentionally narrow: it allows Amphetamine's Power Protect flow to run only `/usr/bin/pmset -a disablesleep 1` and `/usr/bin/pmset -a disablesleep 0` without repeated authentication prompts.

Do not hand-create or broaden this sudoers rule. Use the official signed installer, then validate:

```bash
visudo -cf /private/etc/sudoers.d/amphetamine_PowerProtect
sudo -l | grep -E 'pmset|disablesleep'
```

## Recommended Configuration

Use conservative defaults:

- Start sessions from the menu bar with a timer, not indefinite mode.
- Default timer: `30m` for agent/music sessions.
- Use longer sessions only when the Mac is on a hard, ventilated surface.
- Enable the low-battery auto-end safeguard in Amphetamine preferences.
- Recommended low-battery cutoff: `20%`.
- Keep the menu-bar icon visible and treat it as the primary on/off indicator.
- Show session time in the menu bar when possible.
- For closed-lid sessions, make sure the active Amphetamine session prevents system sleep when the built-in display is closed. Amphetamine's wording may expose this as an "Allow system sleep when display is closed" option; for this workflow, that should be disabled/off during the session.

Do not set up an agent CLI wrapper yet. Amphetamine supports AppleScript automation, so a future wrapper can be built around `osascript` if a concrete agent need appears.

## Daily Use

### Open-lid keep-awake

1. Click the Amphetamine menu-bar icon.
2. Start a timed session.
3. Leave closed-display behavior at the normal/default setting if you only need open-lid keep-awake.

### Lid-closed keep-awake

1. Put the Mac on a hard, ventilated surface.
2. Start a timed Amphetamine session.
3. Configure the session to prevent system sleep when the built-in display is closed.
4. Close the lid only for attended, short use.
5. Reopen the lid and confirm Amphetamine has ended or manually end the session.

### Stop

Use the Amphetamine menu-bar icon to end the active session. If the Mac is not behaving as expected, reopen the lid and verify Amphetamine's menu-bar state before assuming the session is still active.

## Safety Rules

- Do not use closed-lid keep-awake in a backpack, sleeve, bed, couch, under books, under blankets, or anywhere airflow is blocked.
- Do not run heavy CPU/GPU jobs with the lid closed unless the Mac is actively monitored and well ventilated.
- Prefer short, timed sessions for local agents and music.
- Avoid indefinite closed-lid sessions on battery.
- If the Mac feels hot, stop the session and open the lid.
- Treat "putting the laptop in a backpack for a super short time" as a risky edge case. If it must happen, stop the session first unless you are directly monitoring it and the move is momentary.

## Future Automation

Amphetamine can be controlled with AppleScript. A future agent wrapper can inspect the local scripting dictionary and use commands like:

```bash
osascript -e 'tell application "Amphetamine" to start new session'
osascript -e 'tell application "Amphetamine" to end session'
osascript -e 'tell application "Amphetamine" to if not (session is active) then start new session'
osascript -e 'tell application "Amphetamine" to enable closed display mode'
osascript -e 'tell application "Amphetamine" to closed display mode enabled'
```

Do not add this wrapper until there is a real workflow that needs it.

## Validation Checklist

Record validation in the active task before relying on this workflow:

- Amphetamine installed from the Mac App Store.
- Amphetamine launches and shows a menu-bar icon.
- A timed open-lid session starts and stops.
- Low-battery auto-end is configured.
- Power Protect is installed or explicitly not needed.
- A timed closed-display-mode session sets `SleepDisabled=1` while active.
- Ending the session restores `SleepDisabled=0`.
- A short attended closed-lid baseline test keeps music or a harmless local process alive.
- A separate attended closed-lid power-source transition test works: connect and disconnect power or a USB-C power-delivery display while the closed-lid session is active.
- The Mac remains cool enough on a hard, ventilated surface.
- The session can be ended cleanly from the menu bar.
