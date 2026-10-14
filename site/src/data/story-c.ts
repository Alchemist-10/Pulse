// All pair identities below are from the committed synthetic seed, not real
// Patient data. Source: seed/data/identity/patients.csv and
// seed/data/identity/planted_pairs.csv (linked from seed/README.md).
export const reviewPairs = [
  // Order-swap pair: patients.csv:5,92; planted_pairs.csv:2; build.py:322-330.
  // Score 1.000 was calculated with users/service.py:168-252.
  {
    id: "order",
    label: "Token order swap",
    a: { name: "ଶ୍ରୀମତୀ ଭବାନୀ ଦେବି", dob: "1976-12-07", phone: "+91 90000 79547" },
    b: { name: "ଦେବି ଶ୍ରୀମତୀ ଭବାନୀ", dob: "1976-12-07", phone: "+91 90000 79547" },
    expectation: "Known duplicate planted in the seed set",
    score: 1.0,
  },
  // Initials pair: patients.csv:6,100; planted_pairs.csv:3; build.py:341-348.
  // Score 0.688 was calculated with users/service.py:168-252.
  {
    id: "initials",
    label: "Initials vs expanded name",
    a: { name: "Aishani Toor", dob: "1962-01-13", phone: "+91 90000 20757" },
    b: { name: "A. Toor", dob: "1962-01-13", phone: "+91 90000 20757" },
    expectation: "Known duplicate planted in the seed set",
    score: 0.688,
  },
  // Two-day DOB typo pair: patients.csv:9,62; planted_pairs.csv:4; build.py:332-339.
  // Score 0.955 was calculated with users/service.py:168-252.
  {
    id: "dob",
    label: "Two-day DOB typo",
    a: { name: "யூவராஜ் ரீட்டா", dob: "2019-12-10", phone: "+91 90000 30191" },
    b: { name: "யூவராஜ் ரீட்டா", dob: "2019-12-08", phone: "+91 90000 30191" },
    expectation: "Known duplicate planted in the seed set",
    score: 0.955,
  },
  // Sibling near-miss pair: patients.csv:25,81; planted_pairs.csv:6; build.py:350-369.
  // Score 0.075 was calculated with users/service.py:168-252.
  {
    id: "sibling",
    label: "Sibling near-miss",
    a: { name: "ரத்தினம் சஜனி", dob: "2022-01-05", phone: "+91 90000 28322" },
    b: { name: "ஆகாஷ் சஜனி", dob: "2024-01-05", phone: "+91 90000 64609" },
    expectation: "Known non-duplicate planted to check false positives",
    score: 0.075,
  },
  // Second sibling pair: patients.csv:19,75; planted_pairs.csv:5; build.py:350-369.
  // Score 0.174 was calculated with users/service.py:168-252.
  {
    id: "sibling-two",
    label: "Second sibling near-miss",
    a: { name: "स्वर्ण बुरुाहजी", dob: "1965-07-12", phone: "+91 90000 95244" },
    b: { name: "संमानित बुरुाहजी", dob: "1967-07-12", phone: "+91 90000 14987" },
    expectation: "Known non-duplicate planted to check false positives",
    score: 0.174,
  },
] as const;
