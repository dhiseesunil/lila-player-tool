# Insights

# Map-wise observation and insights:
## Insight 1: AmbroseValley is over-centralizing loot, combat, and bot encounters

### Observation
AmbroseValley appears to be strongly center-weighted. Loot is heavily concentrated in the inner regions, and bot-related combat tends to happen around those same zones. Border routes, especially the top-left and bottom-right portions, are comparatively quiet and often contain long stretches of movement with little or no interaction.

### Evidence
- Bot kills frequently occur in the same places where loot events are concentrated.
- Several inner-map routes are crowded with both `Loot` and `BotKill` activity.
- Border areas show much less loot density and fewer combat events.
- Cumulative traffic is fairly broad overall, but the bottom-right portion has very little activity.
- Cumulative kill/death heatmaps indicate the center of the map has the highest combat density.
- Only one match was found with multiple human players on this map, so most pressure appears to come from loot placement and bot routing rather than PvP.

### Why This Matters
This suggests the map is pushing players toward the center too aggressively. If the highest-value routes are too obvious and too dense, players get fewer meaningful pathing decisions. Border areas become underused, reducing map variety and making matches feel less dynamic.

### Recommended Action
- Redistribute loot more evenly toward outer and edge regions, especially low-traffic border zones.
- Add secondary attraction points in underused areas, particularly the bottom-right region.
- Review bot routing so bots pressure more of the map instead of converging too often on central loot-heavy paths.
- Preserve the current variety in player spawn/path start locations, since that already creates healthy initial dispersion.

### Likely Impact
- Better traffic distribution across the full map
- More varied rotations and engagements
- Reduced over-centralization of combat
- Improved usefulness of currently ignored spaces

## Insight 2: GrandRift has healthier loot spread, but combat is heavily concentrated in Mine Pit

### Observation
GrandRift has more balanced loot placement than AmbroseValley, including along border regions. However, actual combat and death events still cluster strongly around Mine Pit and nearby central zones such as Engineer’s Quarter and Labour Quarters.

### Evidence
- Loot appears more evenly distributed across the map, including border paths.
- Bot kills are much less tightly tied to dense loot clusters than in AmbroseValley.
- Most traffic is concentrated around Mine Pit, Engineer’s Quarter, Burnt Zone, and Labour Quarters.
- Most bot kills occur in Mine Pit, with additional activity near Engineer’s Quarter and Labour Quarters.
- Most deaths are concentrated in Mine Pit.
- BotKilled events are relatively rare overall, but when they occur they are frequently centered around Mine Pit.
- No multiplayer human matches were observed on this map in the reviewed sample.

### Why This Matters
The map seems to offer more route choice from a loot perspective, but the gameplay pressure still collapses into a dominant central hotspot. That means the map may be structurally balanced in resource placement while still being behaviorally dominated by one area.

### Recommended Action
- Investigate why Mine Pit attracts so much more combat than surrounding regions.
- Consider adding stronger reasons to stay in or rotate through border-connected areas after looting.
- Test whether bot pathing or objective flow is unintentionally funneling engagements back into Mine Pit.
- Preserve the broader loot distribution, since that is already a strength of this map.

### Likely Impact
- Reduced central choke-point dominance
- Better engagement spread across named regions
- More strategic route diversity after early looting

## Insight 3: Lockdown drives interaction into inner building regions while border spaces remain low-value

### Observation
Lockdown’s activity is concentrated around buildings and inner-map regions. Loot is commonly found near buildings, and bot-related combat also tends to happen in a few specific interior zones. Borderline regions show much less interaction, even though cumulative movement is otherwise spread reasonably well across the map.

### Evidence
- Most loot events occur in the vicinity of buildings.
- Many bot kills happen during or near loot events.
- BotKill and BotKilled events are concentrated in specific inner regions.
- Border areas show little or no meaningful combat activity.
- Cumulative pathing is spread across much of the map, but a few edge zones still see much lower engagement.
- There are fewer bot kills here than on the other maps.
- Some matches contain little or no event data.
- No multiplayer human matches were found on this map in the reviewed sample.

### Why This Matters
Players appear willing to move across the map, but the map is not converting that movement into evenly distributed interaction. When loot and combat are too tied to a small number of interior zones, the outer spaces risk becoming traversal-only areas instead of meaningful gameplay spaces.

### Recommended Action
- Improve the value of edge and borderline zones by introducing more distributed loot or encounter opportunities.
- Review whether building clusters are over-concentrating both resources and bot encounters.
- Investigate the matches with little or no event data to determine whether they reflect telemetry gaps or genuinely uneventful rounds.
- Use the existing broad pathing coverage as a foundation and add more reasons for players to engage outside the inner hotspots.

### Likely Impact
- More meaningful use of edge zones
- Better conversion of movement into interaction
- Stronger encounter variety across the map
- Improved readability of whether low-event matches are design-driven or data-driven
