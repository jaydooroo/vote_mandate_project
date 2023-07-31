# Codebook for merged_nokken_poole

## Variables

The variables are listed as they appear in the data file.

### congress

- **Description**: Integer 1+. The number of the congress that this member's row refers to. e.g. 115 for the 115th Congress (2017-2019)

---

### chamber

- **Description**: It represents the chamber in which the member served, either House, Senate, or President.

---

### district

- **Description**: district number
- \***\*Note\*\***: At-large districts are coded as 0 (zero).(only for senate and house)

---

### state_abbrev

- **Description**: U.S. postal code state abbreviation

---

### bioname

- **Description**: String. Name of the member, surname first. For most members, agrees with the Biographical Directory of Congress.

---

### bioguide_id

- **Description**: String. Member identifier in the Biographical Directory of Congress.

---

### nokken_poole_dim1

- **Description**: Nokken-Poole First dimension estimate.

---

### modified_nokken_poole_dim1

- **Description**: It is basically same with Nokken-Poole First dimension estimate, However,
- it is equal to nokken_poole_dim1 for Republicans and equal to (-1)*(nokken_poole_dim1) for Democrats.
- Other party member has NULL value for this variable. 

---

### special

- **Description**: special election
- Coding

| code    | definition        |
| :------ | :---------------- |
| "TRUE"  | special elections |
| "FALSE" | regular elections |

---

### stage

- **Description**: electoral stage
- **Coding**:

| code  | definition        |
| :---- | :---------------- |
| "gen" | general elections |
| "pri" | primary elections |

- **Note**: Only appears in special cases. Consult original House Clerk report for these cases.

---

### party

- **Description**: party of the candidate (always entirely lowercase)
  - **Note**: Parties are as they appear in the House Clerk report. In states that allow candidates to appear on multiple party lines, separate vote totals are indicated for each party. Therefore, for analysis that involves candidate totals, it will be necessary to aggregate across all party lines within a district. For analysis that focuses on two-party vote totals, it will be necessary to account for major party candidates who receive votes under multiple party labels. Minnesota party labels are given as they appear on the Minnesota ballots. Future versions of this file will include codes for candidates who are endorsed by major parties, regardless of the party label under which they receive votes.

---

### vote_share

- **Description**: It represents the vote shares for the candidate of the respective election they had. (Note: Pre-election votes and general election votes are included to calculate the vote share. Sometimes pre-election is used to select the winner of the election. It is hard to distinguish whether each election is the main election or not. Therefore, everything is included.)

---

### dems_vote_share_district

- **Description**: It represents the total Democratic party vote shares in the particular district (If many other parties support a single candidate, we combine all the votes and consider it as the major party votes).

---

### gop_vote_share_district

- **Description**: It represents the total Republican party vote shares in the particular district (If many other parties support a single candidate, we combine all the votes and consider it as the major party votes).

---

### dems_vote_share_state

- **Description**: It represents the total Democratic party vote shares in the particular state (If many other parties support a single candidate, we combine all the votes and consider it as the major party votes). senate and house has their own seperate value.(calculated by the office seperately)
  - **Note**:
    There are cases where the election has only one candidate. In this case, there is no election, and the winner is considered to have just one vote. This only has a very little effect on the total state votes, which might distort the actual public favor on the parties.

---

### gop_vote_share_state

- **Description**: It represents the total Republican party vote shares in the particular state (If many other parties support a single candidate, we combine all the votes and consider it as the major party votes).senate and house has their own seperate value.(calculated by the office seperately)
  - **Note**:
    There are cases where the election has only one candidate. In this case, there is no election, and the winner is considered to have just one vote. This only has a very little effect on the total state votes, which might distort the actual public favor on the parties.

---

### recent_dems_vote_share_senate

- **Description**: It represents the Democrat vote shares of the Senator with the lowest subterm value (most recent election result of the particular state for a senator).
- based on the instruction 5: d. Create “Most recent senate Democrat vote share” and “Most recent Senate Republican vote share” columns, set equal to the Democrat and Republican vote shares of the Senator with the lowest subterm value.

---

### recent_gop_vote_share_senate

- **Description**: It represents the Republican vote shares of the Senator with the lowest subterm value (most recent election result of the particular state for a senator).
- based on the instruction 5: d. Create “Most recent senate Democrat vote share” and “Most recent Senate Republican vote share” columns, set equal to the Democrat and Republican vote shares of the Senator with the lowest subterm value.

---

### recent_dems_vote_share_house

- **Description**: It represents the Democrat vote shares of the congressman with the most recent election result of the particular state (basically same as dems_vote_share_state for the House election).
- based on the instruction 10: Senators should also have variables indicting total party vote share in most recent House races combined, and same-party vote share for fellow senator in the state.

---

### recent_gop_vote_share_house

- **Description**: It represents the Republican vote shares of the congressman with the most recent election result of the particular state (basically same as gop_vote_share_state for the House election).
- based on the instruction 10: Senators should also have variables indicting total party vote share in most recent House races combined, and same-party vote share for fellow senator in the state.

---

### dems_avg_vote_share_senate

- **Description**: It represents the average Democrat vote shares of the two senators for that state/year.
- based on the instruction 5: Create “Average senate Democrat vote share” and “Average senate Republican vote share” columns, set equal to the average Democrat and Repbulican vote shares of the two senators for that state/year.

---

### gop_avg_vote_share_senate

- **Description**: It represents the average Republican vote shares of the two senators for that state/year. 
- based on the instruction 5: Create “Average senate Democrat vote share” and “Average senate Republican vote share” columns, set equal to the average Democrat and Repbulican vote shares of the two senators for that state/year.

---

### dems_pres_vote_share

- **Description**: democrat vote shares of the most recent presidential election.
- based on the instruction 6: e. This should leave us with D & R vote shares for every presidential election year (divisible by 4); copy data into off-election years (divisible by two but not 4)

---

### gop_pres_vote_share

- **Description**: republican vote shares of the most recent presidential election.
- based on the instruction 6: e. This should leave us with D & R vote shares for every presidential election year (divisible by 4); copy data into off-election years (divisible by two but not 4)

---

### fellow_senate_vote_share

- **Description**:  variable that equals the party vote share in the other senate race from the same state.  
- Suppose, for example, that senators A and B from Colorado won their most recent elections 52%-47% and 55%-41%, respectively.  
- If A is a Republican but B is a Democrat, then the fellow_senate_share variable should equal 41% for senator A and 47% for senator B.  If A and B are both Democrats then fellow_senate_share should equal 55% for senator A and 52% for senator B.
- only senators have this value
### subterm

- **Description**: subterm for senator
- based on the instruction 5: a. Create “subterm” variable 1,2,3 for election year (1), subsequent year (2), sub-subsequent year (3); vote share will be present in subterm 1 but missing in subterms 2 and 3

---

## NOTES:
