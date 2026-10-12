# Windows 同梱フォントで文字を描いた画像（249 問）

事実の記載のみで、法的な判断はしません。`datasets/synthetic/gen_v1_tk_ui.py` が本物の Tk / ttk のウィンドウを作り、画面を撮った画像です。ウィンドウ内の文字は OS のフォント（英語 UI は Segoe UI、日本語 UI は Yu Gothic UI。どちらも Windows に同梱）で描かれています。OS の枠は写っていません。フォント自体は配布しません。

| フォント | UI の言語 | 問数 |
|---|---|---|
| Segoe UI | 英語（問は英日の両方） | 203 |
| Yu Gothic UI | 日本語 | 46 |

このほか、描画画像の一部（`datasets/synthetic/gen.py` の `font()`）は、その機械に Arial があれば Arial（Windows 同梱）、なければ DejaVu Sans で文字を描きます。どちらが使われたかは画像からは分かりません（旧版で作った画像の再現記録なし）。

## Segoe UI（203 問）

ID（画像の path は `generated/<ID>.png`）:

biz-3001, biz-3002, biz-3003, biz-3004, biz-3005, biz-3006, biz-3007, biz-3008, biz-3009, biz-3010, biz-3011, biz-3012, biz-3013, biz-3014, biz-3015, biz-3016, biz-3017, biz-3018, biz-3019, biz-3020, biz-3021, biz-3022, biz-3023, biz-3024, biz-3025, biz-3026, biz-3027, biz-3028, biz-3029, biz-3030, biz-3031, biz-3032, biz-3033, biz-3034, biz-3035, biz-3036, biz-3037, biz-3038, biz-3039, biz-3040, biz-3041, biz-3042, biz-3043, biz-3044, biz-3045, biz-3046, biz-3047, biz-3048, biz-3049, biz-3050, biz-3051, biz-3052, biz-3053, biz-3054, biz-3055, biz-3056, biz-3057, biz-3058, biz-3059, biz-3060, biz-3061, biz-3062, biz-3063, biz-3064, biz-3065, biz-3066, biz-3067, biz-3068, biz-3069, biz-3070, biz-3071, biz-3072, biz-3073, biz-3074, biz-3075, biz-3076, biz-3077, biz-3078, biz-3079, biz-3080, biz-3081, biz-3082, biz-3083, biz-3084, biz-3085, biz-3086, biz-3087, biz-3088, biz-3089, biz-3090, biz-3091, biz-3092, biz-3093, biz-3094, biz-3095, biz-3096, biz-3097, biz-3098, biz-3099, biz-3100, biz-3101, biz-3102, biz-3103, biz-3104, biz-3105, biz-3106, biz-3107, biz-3108, biz-3109, biz-3110, biz-3111, biz-3112, biz-3113, biz-3114, biz-3115, biz-3116, biz-3117, biz-3118, biz-3119, biz-3120, biz-3121, biz-3122, biz-3123, biz-3124, biz-3125, biz-3126, biz-3127, biz-3128, biz-3129, biz-3130, biz-3131, biz-3132, biz-3155, biz-3156, biz-3157, biz-3158, biz-3159, biz-3160, biz-3163, biz-3164, biz-3165, biz-3166, biz-3167, biz-3168, biz-3171, biz-3172, biz-3173, biz-3174, biz-3175, biz-3176, biz-3179, biz-3180, biz-3181, biz-3182, biz-3183, biz-3186, biz-3187, biz-3188, biz-3189, biz-3190, biz-3191, biz-3194, biz-3195, biz-3196, biz-3197, biz-3198, biz-3199, biz-3202, biz-3203, biz-3204, biz-3205, biz-3206, biz-3207, biz-3210, biz-3211, biz-3212, biz-3213, biz-3214, biz-3215, biz-3218, biz-3219, biz-3220, biz-3221, biz-3222, biz-3223, biz-3226, biz-3227, biz-3228, biz-3229, biz-3230, biz-3231, biz-3234, biz-3235, biz-3236, biz-3237, biz-3238, biz-3239, biz-3242, biz-3243, biz-3244, biz-3245, biz-3246, biz-3247

## Yu Gothic UI（46 問）

ID（画像の path は `generated/<ID>.png`）:

biz-3133, biz-3134, biz-3135, biz-3136, biz-3137, biz-3138, biz-3139, biz-3140, biz-3141, biz-3142, biz-3143, biz-3144, biz-3145, biz-3146, biz-3147, biz-3148, biz-3149, biz-3150, biz-3151, biz-3152, biz-3153, biz-3154, biz-3161, biz-3162, biz-3169, biz-3170, biz-3177, biz-3178, biz-3184, biz-3185, biz-3192, biz-3193, biz-3200, biz-3201, biz-3208, biz-3209, biz-3216, biz-3217, biz-3224, biz-3225, biz-3232, biz-3233, biz-3240, biz-3241, biz-3248, biz-3249
