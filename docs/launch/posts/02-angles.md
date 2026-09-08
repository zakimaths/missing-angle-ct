# Post 2: Why angular coverage matters

## LinkedIn

The same number of X-ray views can produce very different CT reconstructions.

This comparison uses one measured Helsinki object and 90 views in each case. The first selection spreads views across the scan. The second takes 90 consecutive views within a narrow angular range. Both images use one SART pass and the same display scale.

The difference shows why measurement count alone is an incomplete description of a reconstruction problem. The directions sampled also determine which structures are well constrained.

I added this comparison to Missing-Angle CT, along with controls for inspecting individual views and repeating the calculation. You can change the selection, compare reference errors and test whether additional correction passes help.

Try the comparison: https://zakimaths.github.io/missing-angle-ct/

Images calculated from HTC2022 measurements, Meaney and colleagues, CC BY 4.0. Neither reconstruction is anatomical ground truth.

## X

Same object. Same 90-view budget. Different angular coverage.

Missing-Angle CT lets you compare spread and consecutive X-ray views, then inspect the reconstruction and its errors.

https://zakimaths.github.io/missing-angle-ct/

## Attachment

Use `overview-pink.png` for an actual screenshot of the comparison in the demo, or the existing `demo/share-card.png` for the larger scientific figure. Credit: Meaney and colleagues, HTC2022, CC BY 4.0.
