import streamlit as st
import pandas as pd
import random
from dataclasses import dataclass
from typing import List, Set

@dataclass
class Subject:
    name: str
    code: str
    faculty: str
    hours_per_week: int
    is_lab: bool = False
    room: str = ""

class TimeSlot:
    def __init__(self, day: int, hour: int):
        self.day = day
        self.hour = hour
        self.subject = None

class TimetableConfig:
    def __init__(
        self,
        days_per_week: int,
        hours_per_day: int,
        lunch_break_start: int,
        lunch_break_duration: int,
        branch: str,
        semester: int,
        year: int
    ):
        self.days_per_week = days_per_week
        self.hours_per_day = hours_per_day
        self.lunch_break_start = lunch_break_start
        self.lunch_break_duration = lunch_break_duration
        self.branch = branch
        self.semester = semester
        self.year = year

class TimetableChromosome:
    def __init__(self, config: TimetableConfig, subjects: List[Subject]):
        self.config = config
        self.subjects = subjects
        self.slots = self._initialize_slots()
        self.fitness = 0
        self.faculty_schedule = {}  # Track faculty schedules
        self.room_schedule = {}     # Track room schedules
        self._generate_random_schedule()

    def _initialize_slots(self) -> List[List[TimeSlot]]:
        return [[TimeSlot(day, hour) for hour in range(self.config.hours_per_day)]
                for day in range(self.config.days_per_week)]

    def _is_slot_available(self, day: int, hour: int, subject: Subject) -> bool:
       
        # Check faculty availability
        if subject.faculty in self.faculty_schedule:
            if (day, hour) in self.faculty_schedule[subject.faculty]:
                return False

        # Check room availability
        if subject.room in self.room_schedule:
            if (day, hour) in self.room_schedule[subject.room]:
                return False

        # Ensure lunch break timing doesn't overlap
        if self.config.lunch_break_start <= hour < self.config.lunch_break_start + self.config.lunch_break_duration:
            return False

        return True

    def _add_to_schedule(self, day: int, hour: int, subject: Subject):
        # Add to faculty schedule
        if subject.faculty not in self.faculty_schedule:
            self.faculty_schedule[subject.faculty] = set()
        self.faculty_schedule[subject.faculty].add((day, hour))

        # Add to room schedule
        if subject.room not in self.room_schedule:
            self.room_schedule[subject.room] = set()
        self.room_schedule[subject.room].add((day, hour))

    def _generate_random_schedule(self):
        
        all_slots = [(day, hour)
                     for day in range(self.config.days_per_week)
                     for hour in range(self.config.hours_per_day)
                     if not (hour >= self.config.lunch_break_start and 
                            hour < self.config.lunch_break_start + self.config.lunch_break_duration)]

        for subject in self.subjects:
            hours_left = subject.hours_per_week
            attempts = 0
            max_attempts = 1000  # Prevent infinite loops
            while hours_left > 0 and attempts < max_attempts:
                attempts += 1
                if subject.is_lab and hours_left >= 3:
                    # Find a slot for a 3-hour lab
                    day, hour = random.choice(all_slots)
                    if (hour + 2 < self.config.hours_per_day and 
                        self._is_slot_available(day, hour, subject) and
                        self._is_slot_available(day, hour + 1, subject) and
                        self._is_slot_available(day, hour + 2, subject)):
                        for h in range(3):
                            self.slots[day][hour + h].subject = subject
                            self._add_to_schedule(day, hour + h, subject)
                        hours_left -= 3
                else:
                    # Find a slot for a 1-hour class
                    day, hour = random.choice(all_slots)
                    if self._is_slot_available(day, hour, subject):
                        self.slots[day][hour].subject = subject
                        self._add_to_schedule(day, hour, subject)
                        hours_left -= 1

    def calculate_fitness(self):
        fitness = 100

        # Check for faculty conflicts
        faculty_slots = {}
        for day in range(self.config.days_per_week):
            for hour in range(self.config.hours_per_day):
                slot = self.slots[day][hour]
                if slot.subject:
                    faculty = slot.subject.faculty
                    if faculty not in faculty_slots:
                        faculty_slots[faculty] = set()
                    if (day, hour) in faculty_slots[faculty]:
                        fitness -= 30  # High penalty for conflict
                    faculty_slots[faculty].add((day, hour))

        # Check for room conflicts
        room_slots = {}
        for day in range(self.config.days_per_week):
            for hour in range(self.config.hours_per_day):
                slot = self.slots[day][hour]
                if slot.subject:
                    room = slot.subject.room
                    if room not in room_slots:
                        room_slots[room] = set()
                    if (day, hour) in room_slots[room]:
                        fitness -= 30  # High penalty for conflict
                    room_slots[room].add((day, hour))

        # Check for lunch break violations
        for day in range(self.config.days_per_week):
            for hour in range(self.config.lunch_break_start, 
                            self.config.lunch_break_start + self.config.lunch_break_duration):
                if self.slots[day][hour].subject:
                    fitness -= 20  # Penalty for scheduling during lunch

        # Check for lab hour continuity
        for day in range(self.config.days_per_week):
            for hour in range(self.config.hours_per_day - 2):
                slot = self.slots[day][hour]
                if slot.subject and slot.subject.is_lab:
                    if (not self.slots[day][hour + 1].subject or 
                        not self.slots[day][hour + 2].subject or
                        self.slots[day][hour + 1].subject != slot.subject or
                        self.slots[day][hour + 2].subject != slot.subject):
                        fitness -= 30  # Penalty for discontinuous lab sessions

        self.fitness = max(0, fitness)
        return self.fitness

def generate_timetable(config: TimetableConfig, subjects: List[Subject]) -> TimetableChromosome:
    population_size = 50
    generations = 100
    mutation_rate = 0.1

    # Initialize population
    population = [TimetableChromosome(config, subjects) for _ in range(population_size)]

    for generation in range(generations):
        # Calculate fitness for all chromosomes
        for chromosome in population:
            chromosome.calculate_fitness()

        # Sort population by fitness (higher is better)
        population.sort(key=lambda x: x.fitness, reverse=True)

        # If perfect fitness is achieved, stop early
        if population[0].fitness == 100:
            break

        # Select the top 50% as parents
        parents = population[:population_size // 2]

        # Create offspring through crossover
        offspring = []
        while len(offspring) < population_size - len(parents):
            parent1, parent2 = random.sample(parents, 2)
            child = TimetableChromosome(config, subjects)

            # Perform crossover: take a random subset of days from each parent
            crossover_point = random.randint(1, config.days_per_week - 1)
            for day in range(config.days_per_week):
                for hour in range(config.hours_per_day):
                    if day < crossover_point:
                        child.slots[day][hour].subject = parent1.slots[day][hour].subject
                    else:
                        child.slots[day][hour].subject = parent2.slots[day][hour].subject

            # Recalculate schedules based on crossover
            child.faculty_schedule = {}
            child.room_schedule = {}
            for day in range(config.days_per_week):
                for hour in range(config.hours_per_day):
                    slot = child.slots[day][hour]
                    if slot.subject:
                        child._add_to_schedule(day, hour, slot.subject)

            # Mutation: swap two random slots
            if random.random() < mutation_rate:
                day1, hour1 = random.randint(0, config.days_per_week - 1), random.randint(0, config.hours_per_day - 1)
                day2, hour2 = random.randint(0, config.days_per_week - 1), random.randint(0, config.hours_per_day - 1)
                slot1 = child.slots[day1][hour1].subject
                slot2 = child.slots[day2][hour2].subject

                # Swap subjects if possible
                if slot1 is not None and slot2 is not None:
                    # Check if swapping causes any conflicts
                    can_swap = True
                    # Check faculty and room for slot1 in new position
                    if slot1.faculty in child.faculty_schedule and (day2, hour2) in child.faculty_schedule[slot1.faculty]:
                        can_swap = False
                    if slot1.room in child.room_schedule and (day2, hour2) in child.room_schedule[slot1.room]:
                        can_swap = False
                    # Similarly for slot2
                    if slot2.faculty in child.faculty_schedule and (day1, hour1) in child.faculty_schedule[slot2.faculty]:
                        can_swap = False
                    if slot2.room in child.room_schedule and (day1, hour1) in child.room_schedule[slot2.room]:
                        can_swap = False

                    if can_swap:
                        child.slots[day1][hour1].subject, child.slots[day2][hour2].subject = slot2, slot1

                        # Update schedules
                        child.faculty_schedule[slot1.faculty].remove((day1, hour1))
                        child.room_schedule[slot1.room].remove((day1, hour1))
                        child.faculty_schedule[slot1.faculty].add((day2, hour2))
                        child.room_schedule[slot1.room].add((day2, hour2))

                        child.faculty_schedule[slot2.faculty].remove((day2, hour2))
                        child.room_schedule[slot2.room].remove((day2, hour2))
                        child.faculty_schedule[slot2.faculty].add((day1, hour1))
                        child.room_schedule[slot2.room].add((day1, hour1))

            offspring.append(child)

        # Create new population
        population = parents + offspring

    # Return the best timetable
    best_timetable = max(population, key=lambda x: x.fitness)
    return best_timetable

def main():
    st.title("Automated Timetable Generator")

    # Sidebar for configuration
    st.sidebar.header("Configuration")
    days_per_week = st.sidebar.number_input("Number of days per week", min_value=1, max_value=6, value=5)
    hours_per_day = st.sidebar.number_input("Number of hours per day", min_value=1, max_value=10, value=7)
    lunch_break_start = st.sidebar.number_input("Lunch break start hour (0-indexed)", min_value=0, max_value=hours_per_day-1, value=3)
    lunch_break_duration = st.sidebar.number_input("Lunch break duration (hours)", min_value=1, max_value=2, value=1)
    branch = st.sidebar.text_input("Branch", "Computer Science")
    semester = st.sidebar.number_input("Semester", min_value=1, max_value=8, value=3)
    year = st.sidebar.number_input("Year", min_value=1, max_value=4, value=2)

    # Initialize session state for subjects
    if 'subjects' not in st.session_state:
        st.session_state.subjects = []

    # Subject input form
    st.header("Add Subject")
    with st.form("add_subject"):
        col1, col2 = st.columns(2)
        with col1:
            subject_name = st.text_input("Subject Name")
            subject_code = st.text_input("Subject Code")
            faculty_name = st.text_input("Faculty Name")
        
        with col2:
            hours_per_week = st.number_input("Hours per week", min_value=1, max_value=10, value=3)
            is_lab = st.checkbox("Is Lab?")
            room = st.text_input("Room Number")
        
        submitted = st.form_submit_button("Add Subject")
        if submitted:
            if subject_name and subject_code and faculty_name and room:
                new_subject = Subject(
                    name=subject_name,
                    code=subject_code,
                    faculty=faculty_name,
                    hours_per_week=int(hours_per_week),
                    is_lab=is_lab,
                    room=room
                )
                st.session_state.subjects.append(new_subject)
                st.success(f"Added subject: {subject_name}")
            else:
                st.error("Please fill in all fields.")

    # Display added subjects
    if st.session_state.subjects:
        st.header("Added Subjects")
        subjects_df = pd.DataFrame([
            {
                "Subject": s.name,
                "Code": s.code,
                "Faculty": s.faculty,
                "Hours": s.hours_per_week,
                "Type": "Lab" if s.is_lab else "Theory",
                "Room": s.room
            }
            for s in st.session_state.subjects
        ])
        st.table(subjects_df)

    # Generate timetable button
    if st.button("Generate Timetable") and st.session_state.subjects:
        config = TimetableConfig(
            days_per_week=int(days_per_week),
            hours_per_day=int(hours_per_day),
            lunch_break_start=int(lunch_break_start),
            lunch_break_duration=int(lunch_break_duration),
            branch=branch,
            semester=int(semester),
            year=int(year)
        )
        
        with st.spinner("Generating timetable... This may take a moment."):
            timetable = generate_timetable(config, st.session_state.subjects)
        
        # Check if the best timetable has perfect fitness
        if timetable.fitness < 100:
            st.warning("Could not generate a perfect timetable. Please check constraints or add more flexibility.")
        
        # Create timetable display
        st.header("Generated Timetable")
        
        # Header info
        st.write(f"**Branch:** {branch} | **Semester:** {semester} | **Year:** {year}")
        
        # Create timetable data
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'][:config.days_per_week]
        time_slots = [f"{8 + hour}:00 - {9 + hour}:00" for hour in range(config.hours_per_day)]
        
        data = []
        for hour in range(config.hours_per_day):
            row = [time_slots[hour]]
            for day in range(config.days_per_week):
                slot = timetable.slots[day][hour]
                if config.lunch_break_start <= hour < config.lunch_break_start + config.lunch_break_duration:
                    cell = "**Lunch**"
                elif slot.subject:
                    cell = f"{slot.subject.name}\n({slot.subject.code})\n{slot.subject.faculty}\n{slot.subject.room}"
                else:
                    cell = "-"
                row.append(cell)
            data.append(row)
        
        df = pd.DataFrame(data, columns=['Time'] + days)
        st.table(df)

        # Display faculty details
        st.header("Faculty Details")
        faculty_df = pd.DataFrame([
            {
                "Faculty Name": s.faculty,
                "Subject": s.name,
                "Subject Code": s.code,
                "Room": s.room
            }
            for s in st.session_state.subjects
        ])
        st.table(faculty_df)

    # Option to reset subjects
    if st.button("Reset Subjects"):
        st.session_state.subjects = []
        st.success("All subjects have been reset.")

if __name__ == "__main__":
    main()
