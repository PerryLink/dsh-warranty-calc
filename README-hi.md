# dsh-warranty-calc — वारंटी अवधि और दावा राशि की संगति की जाँच

`dsh-warranty-calc` वारंटी दावों का एक रजिस्टर पढ़ता है — डीलर हेडर और प्रत्येक दावे की एक पंक्ति — और उसी रजिस्टर के अंकगणित तथा अवधि की आंतरिक संगति की जाँच करता है: क्या प्रत्येक दावे में दावा क्रमांक या पुर्ज़े का नाम दर्ज है, क्या दावे की तारीख रजिस्टर में लिखी वारंटी समाप्ति तिथि के भीतर पड़ती है, क्या दावे के समय की माइलेज संख्या के रूप में पढ़ी जा सकती है और रजिस्टर में लिखी माइलेज सीमा से अधिक नहीं है, क्या दावा राशि मात्रा × इकाई मूल्य के बराबर है, क्या बिक्री तिथि दावे की तारीख के बाद नहीं है, और क्या दावा क्रमांक दोहराए नहीं गए हैं।

## यह किन सवालों का जवाब देता है

| आपका सवाल | इसका जवाब |
|---|---|
| रजिस्टर में वारंटी समाप्ति तिथि दर्ज नहीं है। क्या दावे की तारीख की जाँच चुपचाप पास हो जाती है? | नहीं। वारंटी समाप्ति का कॉलम खाली होने पर `WC-002` स्वयं `skipped` में दर्ज होता है: यह कोई अवधि न मान लेता है न बिक्री तिथि से निकालता है। कॉलम भरा होने पर यह केवल देखता है कि दावे की तारीख आपकी लिखी बिक्री तिथि और समाप्ति तिथि के बीच पड़ती है, और अंतर मिलने का अर्थ यह है कि यह आपके ही रजिस्टर की अवधि से मेल नहीं खाता — यह नहीं कि दावा वारंटी से बाहर है। |
| दावा राशि मात्रा × इकाई मूल्य के बराबर नहीं है — क्या यह पकड़ में आता है? | हाँ। `WC-005` उस पंक्ति को दर्ज करता है जहाँ `claimAmount`, `quantity` × `unitPrice` से 0.01 की सहनशीलता से अधिक हट जाता है। यह केवल पुर्ज़ों की राशि पर लागू होता है: यदि आपका रजिस्टर पुर्ज़े + श्रम − कटौती के हिसाब से निपटान करता है (`laborHours`, `laborRate`, `deductible` अलग कॉलम हैं), तो यह नियम अंतर दर्ज करेगा — `resultField` को पुर्ज़ा-राशि कॉलम पर लगाएँ या नियम बंद कर दें। यह नहीं आँकता कि इकाई मूल्य उचित है या पुर्ज़ा बदला जाना ही चाहिए था। |
| दावे के समय की माइलेज `48,600 公里` लिखी है — क्या यह पढ़ी जाएगी? और सीमा से अधिक हो तो? | हाँ। `WC-003` उसमें से संख्यात्मक भाग लेता है, इसलिए `48600` और `48,600 公里` दोनों पढ़े जाते हैं; केवल वह माइलेज दर्ज होती है जिसे पढ़ा न जा सके, और यह नहीं आँकता कि सीमा से अधिक है या नहीं। वह तुलना `WC-004` करता है, जो केवल रजिस्टर में लिखी `warrantyMiles` सीमा से मिलाता है — कोई संख्या भीतर से थोपी नहीं गई — और उसका निष्कर्ष «आपकी दर्ज सीमा से अधिक» है, «वारंटी से बाहर» नहीं: समय और माइलेज दो स्वतंत्र सीमाएँ हैं, जो पहले पूरी हो वही। |
| एक ही दावा क्रमांक दो पंक्तियों में आया है। | `WC-007` दोहराए गए `claimNo` को दर्ज करता है और तुलना में रिक्त स्थान छोड़ देता है, क्योंकि दोहराव से दावा राशि का जोड़ दो बार गिना जाता है और निर्माता पंक्ति का मिलान नहीं कर पाता। एक ही दावा अलग-अलग पुर्ज़ों के लिए कई पंक्तियों में दर्ज करना सामान्य है: पुर्ज़े के नाम कॉलम में उन्हें अलग दिखाएँ। |
| किसी पंक्ति में न दावा क्रमांक है न पुर्ज़े का नाम। | `WC-001` उस पंक्ति को केवल तब दर्ज करता है जब `claimNo` और `partName` दोनों में से कोई भी न भरा हो: दोनों में एक होना ही पर्याप्त है। यह देखता है कि न्यूनतम पता-लगाने योग्य सूचना दर्ज है, यह नहीं कि दावा वारंटी के दायरे में है या स्वीकार किया जाना चाहिए। |
| बिक्री तिथि दावे की तारीख से बाद की है। | `WC-006` रजिस्टर की दोनों तारीखों की तुलना करता है और जहाँ `saleDate`, `claimDate` के बाद है वह पंक्ति दर्ज करता है। आरंभ तिथि आपके बिक्री-तिथि कॉलम से ली जाती है: नियम जिस धारा का हवाला देता है वह केवल बीजक तिथि और सुपुर्दगी तिथि को आरंभ बिंदु बताती है, यह नियम आपके लिए कोई चुनाव नहीं करता और वास्तविक आरंभ निर्माता की प्रतिबद्धता के अनुसार होता है। जो तारीख पढ़ी न जा सके वह अलग से दर्ज होती है, चुपचाप छोड़ी नहीं जाती। |

## यह किन मानकों पर आधारित है

| दस्तावेज़ | संख्यांक | इन्हें उद्धृत करने वाले नियम |
|---|---|---|
| 《家用汽车产品修理更换退货责任规定》 | 市场监管总局令第43号（2021 年 7 月 22 日公布，自 2022 年 1 月 1 日起施行） | WC-001, WC-003, WC-005, WC-006, WC-007 |
| 各厂商质保政策与三包规定（本机构配置） | 无统一标准（本条依据为台账写明的质保期） | WC-002 |
| 各厂商质保政策（本机构配置） | 无统一标准（本条依据为台账写明的里程上限） | WC-004 |

**Boundary:** this plugin checks a **质保索赔台账** for arithmetic and period self-consistency — that a claim
records its number or part name, that the claim date falls inside the warranty end date the register states,
that mileage parses and does not exceed the mileage cap the register states, that the claim amount equals
quantity × unit price, that the sale date does not follow the claim date, and that claim numbers do not repeat.
It does **not** decide whether a claim should be accepted, whether a failure is covered, or whether it was
caused by misuse or normal wear.

> ### ⚠️ Warranty policy is the manufacturer's, and this pack does not pretend to quote one
>
> Period length, mileage cap, labour rates and deductibles are set by **each manufacturer's warranty policy**
> and by the three-guarantee rules for the relevant product category. **No unified standard exists**, so every
> rule's `basis` says exactly that and stays at `warn` or `info`.
>
> Three consequences are worth knowing before trusting a finding:
>
> - **The plugin never derives a warranty end date.** It does not compute "sale date + 36 months", because
>   months vary in length and the period may start at delivery or at registration rather than at sale — a
>   computed date would look precise while possibly being wrong. **You work the date out under the applicable
>   policy and record it in the 质保期截止日 column**, and `WC-002` compares against that.
> - **`WC-004`'s mileage cap comes from the register too.** No figure is built in, and a finding means "above
>   the cap you recorded", never "out of warranty" — time and mileage are **independent limits, whichever comes
>   first**, and policies differ on what happens past either.
> - **`WC-005` covers parts only.** Real claim amounts often add labour and material and subtract a deductible,
>   and this register has separate columns for those. A register settling as "parts + labour − deductible" will
>   report a difference; repoint `resultField` at a parts-amount column, or disable the rule.
>
> **Every `excerpt` in the rule pack says, in so many words, that the clause text was not obtained.** When the
> texts are in hand, replace each `excerpt` with the real clause and raise `kind` to `direct`.

## Compatibility

| सतह | स्थिति |
|---|---|
| Harness | peer रेंज `>=0.1.2-rc.1 <0.2.0 \|\| >=0.2.0-0 <0.3.0` — `0.2.0-rc.2` और `0.2.1-alpha.1` दोनों को स्वीकार करने के लिए सत्यापित। **`engines.dsh` जानबूझकर घोषित नहीं**: इसका कोई पाठक नहीं और यह किसी होस्ट को अस्वीकार नहीं कर सकता |
| Node | `^22.19.0 || >=24.0.0` |
| प्लेटफ़ॉर्म | सभी (शुद्ध ESM; कोई नेटिव कोड नहीं, कोई नेटवर्क नहीं, कोई मॉडल कॉल नहीं) |
| टूल मोड | `native`, `ptc` और `both` में काम करता है; पूरे फ़ोल्डर के लिए `ptc` चुनें |

## What it does

नियम-सूची, फ़ील्ड और विस्तृत व्यवहार [README.md](README.md#what-it-does) (अंग्रेज़ी मुख्य संस्करण) में हैं। यह प्लगइन केवल उद्धृत धाराओं के सामने शाब्दिक अंतर सूचीबद्ध करता है और हर न चल पाई जाँच को `skipped` में बताता है।

## Install

```sh
dsh plugin --profile <name> add dsh-warranty-calc
dsh --profile <name> --dump-config | grep 'dsh-warranty-calc'
```

## Configuration

सभी समायोज्य पैरामीटर `src/config.ts` की Schemastery स्कीमा में हैं, इसलिए कोड बदले बिना `cordis.yml` से बदले जा सकते हैं; प्रति-नियम सीमाएँ `rules/` के नियम-पैक में हैं।

| कुंजी | प्रकार | डिफ़ॉल्ट | विवरण |
|---|---|---|---|
| `rulesFile` | string | `rules/warranty-calc.yaml` | नियम-पैक का पथ, पैकेज रूट के सापेक्ष |
| `disabledRules` | string[] | `[]` | बंद करने वाले नियम id; प्रत्येक `skipped` में दिखता है |
| `onlyRules` | string[] | `[]` | केवल ये नियम चलाएँ; खाली होने पर सभी नियम चलते हैं |
| `skipNotes` | string | `""` | हर `skipped` कारण के आगे जोड़ी जाने वाली टिप्पणी |
| `timeoutMs` | number | `120000` | उपकरण का सहकारी समय-सीमा बजट |

## Material format

JSON या YAML स्वीकार्य है। पूरा फ़ील्ड उदाहरण [README.md](README.md#material-format) (अंग्रेज़ी मुख्य संस्करण) में है। पढ़ने की परत में फ़ील्ड वैकल्पिक हैं और जाँच इंजन उन्हें सत्यापित करता है, इसलिए आंशिक निर्यात पर क्रैश के बजाय "अनुपस्थित" श्रेणी के निष्कर्ष मिलते हैं।

## Rule sources

नियम-डेटा कोड से अलग है: प्रत्येक नियम में दस्तावेज़, संख्या, स्रोत की अपनी क्रमांकन-प्रणाली के अनुसार धारा, शब्दशः उद्धरण और स्रोत URL होता है। लोडर लागू करता है कि उद्धरण कम से कम आठ अक्षरों का वास्तविक उद्धरण हो, और जिस जाँच का आधार केवल सामान्य सिद्धांत (`kind: derived-from-principle`, अधिकतम `warn`) या स्थानीय नीति (`kind: institutional-configuration`, अधिकतम `info`) हो, उसे कभी `error` घोषित न किया जाए।

सत्यापित सीमाएँ और जान-बूझकर **न** कहे गए निष्कर्ष [README.md](README.md#rule-sources) (अंग्रेज़ी मुख्य संस्करण) और `rules/evidence/` में हैं।

## Troubleshooting

- **प्लगइन इंस्टॉल हो गया पर टूल दिखता नहीं**: जाँचें कि `main` `lib/index.mjs` पर जाता है और `pnpm run build` ने उसे बनाया है।
- **`dsh plugin add` असंगत बताकर मना करता है**: peer range `0.1.x` और `0.2.x` दोनों को कवर करती है; बाहर होने पर स्पष्ट छूट दें: `dsh plugin --profile <name> allow-version <pkg@ver> --dsh-version <runtime> --accept-risk`।
- **कोई नियम नहीं चला**: `skipped` सरणी देखें।
- **`check` में `manifest-peers` विफल दिखता है**: यह `dsh-plugin-dev` की ज्ञात अपस्ट्रीम समस्या है; रनटाइम इंस्टॉल के समय अनुकूलता लागू करता है।
- **समय खिसका हुआ लगता है**: सारी गणना दिए गए स्ट्रिंग पर वॉल-क्लॉक है।

## Development

```sh
pnpm install
pnpm run typecheck
pnpm test
pnpm run build
node ../scripts/sync-shared.mjs dsh-warranty-calc
```

अंतिम कमांड `../_shared` का साझा किट `src/shared/` में कॉपी करता है; हर साझा बदलाव के बाद इसे दोबारा चलाएँ।

## License

[Apache License 2.0](LICENSE) © 2026 dsh-warranty-calc contributors.
