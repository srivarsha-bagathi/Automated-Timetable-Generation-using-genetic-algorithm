# Automated-Timetable-Generation-using-genetic-algorithm


Output will be generated:
1️. User Input Collection:
Users enter subjects, faculty details, room numbers, time slots, and constraints through the Streamlit UI.

2️.Timetable Initialization:
A randomly generated timetable is created as an initial population using a chromosome-based approach.

3️. Genetic Algorithm Execution:
  Fitness Evaluation: Each timetable is assessed based on faculty availability, room constraints, lab continuity, and lunch breaks.
  Selection: The best-performing timetables (higher fitness scores) are chosen.
  Crossover & Mutation: Parent timetables are combined and modified to create new schedules, ensuring diversity and conflict resolution.
  Iteration & Optimization: The process repeats for multiple generations until an optimal timetable is found.
  
4️. Timetable Display & Visualization:
The final optimized timetable is structured in a tabular format and displayed using Pandas DataFrame in Streamlit.
The timetable includes time slots, subjects, faculty names, room numbers, and lab sessions.
A separate faculty-wise schedule is also generated for better clarity.

5️. User Interaction & Modifications:
Users can regenerate the timetable if conflicts persist.
The system provides real-time warnings if a perfect timetable isn’t achievable under given constraints.
Option to reset subjects and input details again for a fresh generation cycle.
