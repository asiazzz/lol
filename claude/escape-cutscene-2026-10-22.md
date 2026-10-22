# Escape cutscene: build plan (22 Oct 2026, NOT BUILT YET)

This chat ran in a cloud session that had no Roblox Studio connection, so nothing was changed in the game. Build it from a session on the user's PC: the Claude Desktop app, or `claude remote-control` in a terminal there. That session has the Studio tools. First read the project status and the GDD as usual, then this plan.

## The user's request (22 Oct)

> make a cool cutscene when the player escapes from the house; As soon as the player exits the door, play this cutscene:
> The player is being chased with the monster behind him, he is running fast towards the gate and manages to successfully run away from him. The monster starts sobbing from anger and sadness.

## Where it hooks in (from the GDD)

- Escaping already happens at the right moment. "Everyone who reaches the porch escapes": Markers.EscapeZone is on the porch, just outside the front door. The porch trigger also checks the player walked through the door area within the last 3 s, and the front door must be open on the server.
- The scene starts at that existing escape moment, in RoundService's escape check (checkEscapes, which calls MissionService.OnEscape). No new trigger is needed.
- The round ends when everyone has escaped or become a ghost, or 90 s after the front door opens (State Escape). Solo: "run onto the porch: the results screen appears".

## What the player sees (about 16.5 s, only on the escaping player's screen)

Third person, letterboxed, skippable (the same Skip button and VoteSkip). The runner is a local copy of the player's own avatar. The monster is a local StalkerVisual, as in the doorbell cutscene. The real Verity stays inside, hunting anyone still playing.

| # | Time (s) | Shot | What happens |
|---|---|---|---|
| 1 | 0.0–1.6 | **Burst out.** Low camera on the path at (3.5, 0.9, 74) looking up at the doorway (0, 3.5, 41), FOV 60 | You sprint off the porch and down the steps toward the camera (run clip 1.3x, 16 studs/s). At 0.4 s the monster crashes out of the dark doorway behind you (Chase clip 1.35x, 18 studs/s) with CutsceneRoar 0.9x. ChaseMusic starts from the top. |
| 2 | 1.6–3.4 | **Run!** Tracking from the front: camera 7 studs ahead of you, 1.5 to your left, at head height, sliding back with you, light handheld shake, FOV 55 | You fill the foreground. The monster closes from about 8 to 5 studs behind you, arms reaching. Its footfalls thud (Step) and you pant. |
| 3 | 3.4–5.0 | **The claw.** Side tracking from beyond the west flower bed (x −17, y 3.2), slow motion: world time eases to 0.3x for about 1 s | The monster lunges (CutsceneLunge 0.6x). Its claw swipes past your back by a hand's width (a whoosh); you duck forward and keep running. Two heartbeat thumps, then back to full speed near the gate. |
| 4 | 5.0–6.6 | **The gate.** From the pavement outside, (−3, 2.2, 116.5), looking back through the open iron gate, FOV 55 | You burst through the gate, spin round and swing both iron leaves shut (0.22 s): CLANG. The chase music cuts dead on the clang. 0.15 s later the monster slams into the bars: the gate shudders (±3°, settling over 0.6 s), rattles, and the camera shakes. |
| 5 | 6.6–8.6 | **The bars.** Close on the monster from the street side, camera (0.8, 4.8, 115) looking at its head | It grips the bars and rattles them three times. Then it roars right at you: CutsceneRoar 0.85x and CutsceneRoarBoom, the dark flash (20, 0, 4), a shake. You back away across the pavement. |
| 6 | 8.6–14.0 | **It cries.** Wide from across the road, camera (−7, 3, 128.5), FOV 42 slowly pushing in to 36 | You are in the foreground on the pavement, hands on knees, panting. Behind the bars the roar breaks into a sob. The monster slumps against the gate (forehead on the bars, or down on its knees if the rig has leg bones), hands over its face, shoulders heaving, big cartoon tears dripping. Twice (10.3 s, 12.0 s) it pounds the gate with a fist and growls in frustration, then sobs again. The sob is deep (pitched down), like a big sad beast. |
| 7 | 14.0–16.5 | **Getaway.** Crane up and back to (−12, 24, 148), looking at the house | You jog off east along the pavement. The monster is small at the gate, still sobbing (fading), with the wind. Fade to black from 15.7 s, then the normal flow: the Results card if the round is over, otherwise whatever escaped players get now. |

Reduced scares: no roars, flash or shake from the monster (the gate's shudder stays), GrowlSoft instead of the growls, no lunge sound. The sob stays, because it is sad, not scary.

## Build list

### Server (RoundService, GameConfig)

1. At the existing escape point, after the current bookkeeping (Escaped attribute, OnEscape, rewards): `SetFrozen(player, true)`, flashlight off (`FlashlightService.SetOn(player, false)`), `round.EscapeScenes[player] = os.clock()`, then `Cutscene:FireClient(player, "Escape", { From = root CFrame })`.
2. The scene ends on that player's VoteSkip (accept it while `round.EscapeScenes[player]` is set, in Playing or Escape) or after `GameConfig.Round.EscapeSceneLength` (24 s, read live). Then run whatever already happens to an escaped player (check what that is), unfreeze if they can walk there, clear the entry and `Cutscene:FireClient(player, "EscapeEnd")`.
3. Round end: before `setState("Results")`, wait until `round.EscapeScenes` is empty or every entry has hit the cap, so the last player out (and every solo player) sees the whole scene before the Results card. The 90 s escape window ending mid-scene waits the same way.
4. `GameConfig.Round.EscapeScene = true` turns the scene on or off; `EscapeSceneLength = 24`.
5. Leavers: clear their entry on PlayerRemoving.

### Client (CutsceneController and its neighbours)

1. Cutscene "Escape" → `PlayEscape(data)` → `begin(escapeTimeline, data)`. Use the shared scripted camera BIND, the letterbox and Skip, as the arrival does. "EscapeEnd" → `FinishEscape()`: cleanup, camera back, fade in.
2. Hiding: `hideCharacters()` for every player including yourself (your real character stands frozen on the porch). Also set LocalTransparencyModifier 1 every frame on the real Verity (Runtime.Monster), so there are never two monsters.
3. The runner: set `character.Archivable = true`, Clone, then put Archivable back. Remove scripts, the held-item model and any DeliveryBag. Anchor its HumanoidRootPart, set Humanoid.DisplayDistanceType to None, name it "EscapeRunner" and parent it to workspace.LocalCutscene. Play the avatar's own run and idle animations from the copy's Animator, using the Animate script's values (`Animate.run.RunAnim`, `Animate.idle.Animation1`), with an R6 fallback.
4. Movement is kinematic, so timing is exact and nothing collides (the invisible solid Fence.Gate doesn't matter). One path, sampled by arc length like the restaged intro's Bezier: your porch position → (0, y, 52) at the top of the porch steps → (0, y, 109.4) at the gate → (0.6, y, 114) on the pavement, then the back-off and the jog east. Floor height comes from a downward raycast per sample (porch → path → pavement), excluding LocalCutscene and characters, smoothed. The monster rides the same path at `s_runner − gap(t)`: gap 9 at the burst, 5 by 3.4 s, 1.0 at the claw (about 4.2 s), then it stops at z 108.8 when the gate shuts.
5. Slow motion: one world-time scale multiplies movement dt, the BoneAnimator steps, the runner's AnimationTrack speeds (AdjustSpeed) and the lunge sound's speed.
6. The gate: turn `Exterior.Garden.IronGate.LeafWest` and `LeafEast` locally about their Hinge attributes, the way gateSway already turns LeafEast. Go from OpenAngle to shut over 0.22 s (Quad In), then the shudder. Put both back to OpenAngle in cleanup, Skip included. The server never moves the leaves.
7. The swing: as the runner turns 180° to face the gate, both arms reach back for 0.3 s. Use a pose on the shoulders written to joint.Transform in PreSimulation, the arrival's wave/scratch mechanism, as a new "slam" pose.
8. The monster: a StalkerVisual clone like the doorbell cutscene's (BoneAnimator, HUNCH_POSE, pivot at floorY + PivotHeight 4.2), with new clips (below). Its footfalls play Step 3D.
9. Tears: every 0.45 s one drop from each eye. Each drop is a 0.2-stud light blue Glass ball (150, 200, 255) placed from the head bone's TransformedWorldCFrame (±0.25 sideways, a little forward; check which axis is the face). It falls under 40 studs/s² for 0.6 s, shrinking, then is destroyed. This reads as crying for young kids even with the grinning head.
10. Look and sound: AtmosphereController uses the Outside look while the scene runs (a local override, because the round is in Escape with Power true), with OutsideWind on. MusicController turns the escape music off, plays ChaseMusic with SetLoop from the top at 0 s, and stops it dead at the clang (the user likes hard cuts). After that only sobs, wind and the gate.
11. CharacterLightController: add LocalCutscene's EscapeRunner to its targets, so the runner is lit on high graphics.
12. Studio-only Workspace attribute `EscapeHold` (a list of "Burst", "Claw", "Slam", "Roar", "Sob") holds those moments 8 s each for screenshots, like IntroHold.

### The monster's new clips

Bake KeyframeSequences like the Reach clip: all 11 bones keyed in every keyframe (hips, spine, spine1, chest, neck, neck1, head, upper_arm.L/R, forearm.L/R), CubicV2 easing. Store them with the clips StalkerVisual already uses.

Starting values in degrees (x, y, z). The signs follow the rig facts in the status doc's working notes. Tune them in the pose lab.

| Clip | Pose |
|---|---|
| Grip | spine −4, spine1 −4, chest −2, neck −4, head (6, 0, 0); upper_arm.L (−135, 0, −16), upper_arm.R (−135, 0, 16); forearms (−30, 0, 0). Rattle: chest x ±3 and upper arms x ±6 at 5 Hz, in 0.3 s bursts. |
| Roar | Grip, plus chest +6, neck +8, head (−18, 0, 0): head thrown back (check the sign). |
| Sob (0.9 s loop) | hips −12, spine −16, spine1 −12, chest −10 ±4 (the heave), neck −10, neck1 4, head (20, 0, ±6 shake); upper_arm.L (−105, 0, 14), upper_arm.R (−105, 0, −14) (forward and in); forearms (−125, 0, 0) (hands to the face). |
| Pound (0.5 s, right arm) | upper_arm.R (−160, 0, 10) with forearm.R −70, dropping to (−70, 0, 10) with forearm −10 at 0.15 s: the hit (gate shudder and growl). |
| Kneel (only if the rig has thigh and shin bones; check the Walk clip's bones) | thighs x −80, shins x 100, pivot down about 1.6 studs over 1.2 s. Without leg bones: a standing hunch with its forehead on the bars. |

### Sounds to find

Use only Roblox-licensed ProSoundEffects/APM clips or the user's own uploads. Search with search_asset, confirm each with GetProductInfo and PreloadAsync, and judge them with the AudioAnalyzer spectrum method from 21 Oct. Every new Sound gets a Source attribute.

| Name | Search for | Notes |
|---|---|---|
| MonsterSob, MonsterSob2 | "Monster Crying (SFX)", "Creature Whimper (SFX)", "Crying Sobbing (SFX)", "Ogre Groan (SFX)" | Play at 0.6–0.75x so it sounds deep and big, not like a person. Mostly under 2 kHz. |
| GateSlam | "Metal Gate Slam (SFX)", "Iron Gate Close (SFX)" | 3D at the gate. |
| GateRattle | "Metal Fence Rattle (SFX)", "Gate Rattle (SFX)" | 3D at the gate, one per rattle or pound. |
| RunPant | "Heavy Breathing Running (SFX)" | The runner out of breath. Keep it neutral (any avatar). |
| ClawWhoosh | "Whoosh Swipe (SFX)" | The near miss. |

Reused: CutsceneRoar, CutsceneRoarBoom, CutsceneLunge, CutsceneGrowl (GrowlSoft with Reduced scares), Step, ChaseMusic, OutsideWind and the game's heartbeat sound.

## Check these in Studio first (not in the GDD)

1. RoundService's escape code: what happens to an escaped player right after (moved somewhere, spectating, left on the porch?) and how the round end reaches Results.
2. What the Escape state plays (escape music) and which look AtmosphereController uses then.
3. Where StalkerVisual comes from, the BoneAnimator calls and where its clips live; whether the rig has leg bones.
4. The gate leaves: which angle is shut, and which way they swing. If they open toward the street, the swing-shut gesture reads naturally.
5. Each camera's path with GetPartBoundsInRadius, as for the arrival: the two front trees, the lanterns at x ±7.9, the roses, the hedge (z 107.4–109.6), the bins at (8.8, 112) and (11.4, 112).
6. The player's sprint speed and Verity's ChaseSpeed, so the speeds feel like the game.
7. How a held item is attached to the character, so the runner copy carries nothing.

## Test plan

- A quick way to the escape: TestSkipIntro true, TestMonsterOff true, and a helper that opens the front door or starts the Escape state (check what exists). Then walk out onto the porch. Use EscapeHold for screenshots.
- Check:
    - The runner matches the avatar and carries nothing.
    - Every other player and the real Verity are hidden.
    - The runner is lit at graphics 10.
    - The gate shuts, shudders and is open again afterwards.
    - Skip works mid-scene and puts everything back.
    - Reduced scares behaves as above.
    - Solo: the Results card comes after the scene.
    - Test > Clients and Servers with 2 players: one escapes while the other plays on and never sees the scene.
    - Output is clean.
- Afterwards, as always: restore the profile and the *_Studio leaderboards, reset the Test* attributes, and remove EscapeHold and any helpers.

## Choices by Claude (easy to change)

- How you get away: you swing the iron gate shut behind you and the monster crashes into it. The gate stands open all night and creaks, so it pays off. Other options: it stops at the gate as if it can't leave Verity's grounds, or you simply outrun it down the street.
- Third person (you watch yourself run), unlike the first-person doorbell cutscene, because the request describes seeing the player chased.
- A staged local monster rather than the real Verity, so the scene always plays the same and the real one keeps hunting players still inside.
- One slow-motion near miss, the monster's roar at the bars before it breaks down, two angry fist pounds between sobs (anger and sadness), and cartoon tears for the young audience.
- Every player who escapes sees their own scene, alone. Others never see it.
- No player line. If wanted, the runner could say something at the end ("I made it...!"), in the user's own recording like the arrival lines.

## For the status doc's "Next step"

"Escape cutscene (22 Oct, the user's request): planned in claude/escape-cutscene-2026-10-22.md (repo asiazzz/lol, branch claude/quirky-carson-5856tu), NOT built: that chat had no Studio connection. Build it from a session on the user's PC, following the plan, then add GDD section 50 and a checklist row."
