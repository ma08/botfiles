we now have run the setup.sh script to setup the codex skill from the botfiles repository.

now we want to make sure the skills are present in away such that we can use them in any machine

refactor any machine specific code/instructions/setup in codex skills to be more universal (let's support things to work at lesat on the ladduu-dev-ml-vm machine)

we follow these patterns across all the machines:
- botfiles repository is present at ~/pro/botfiles
- personal OS repository is present at ~/pro/personal_os (this generally has some scripts that are used in skills sometimes)


relevant context folders/files:
- /Users/sourya4/pro/personal_os/README.md
- /Users/sourya4/pro/personal_os/context/projects.md
- /Users/sourya4/pro/personal_os/context/daily/2026-02-11/standardize-save-task-status-skill/
- /Users/sourya4/pro/personal_os/context/daily/2026-02-10/setup-remote-workstation

also let's start having a high-level AGENTS.md file ~/pro/botfiles/codex that is symlinked from ~/.codex/AGENTS.md (we should enable this in setup.sh script like we do for CLAUDE.md) counterpart (right now /Users/sourya4/.claude/CLAUDE.md -> /Users/sourya4/pro/botfiles/claude/CLAUDE.md)


also let's update the codex' skills to be in sync with the claude skills counterparts (in case there's any drift)