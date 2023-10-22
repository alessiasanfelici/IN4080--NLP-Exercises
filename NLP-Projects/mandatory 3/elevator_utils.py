
import tkinter as tk
import time, random, string
import dataclasses
import numpy as np

   
@dataclasses.dataclass
class DialogueTurn:
    """Representation of a dialogue turn (from the user or the system)"""
    speaker_name: str
    utterance : str
    timestamp: int = time.time()
    confidence: float = 1.0
    
    
class TalkingElevatorGUI(tk.Frame):
    """Very simple, simulated talking elevator for the IFI building."""
    
    def __init__(self, elevator, window_size="600x500", speed=1.0):
        """Initialises the elevator GUI. Speed refers to the time taken to move from
        one floor to the next in the GUI, in second."""

        self.elevator = elevator
        
        self.speed = speed
                
        self.root = tk.Tk()
        self.root.title("Talking Elevator")
        self.root.geometry(window_size)
        self.root.focus_force()
        
        tk.Frame.__init__(self)

        self._add_elevator()
        self._add_chat()
        
        
    def start(self):
        """Starts the GUI"""
        self.mainloop()
        
        
    def _add_elevator(self, nb_floors=10):
        """Adds widgets representing the elevator in the IFI building"""
        
        elevator_frame = tk.Frame(self.root)
        elevator_frame.pack(side=tk.LEFT)
        
        elevator_text = tk.Label(elevator_frame, text=" Elevator (current\nposition in red):\n")
        elevator_text.pack()
        
        self.floors ={}
        for i in range(nb_floors, 0, -1):
            color = "white" if i!=self.elevator.cur_floor else "red"
            self.floors[i] = tk.Label(elevator_frame, text="%i"%i, width=5, height=2, borderwidth=2, 
                                      relief="groove", bg=color)
            self.floors[i].pack()
        
        status_box = tk.Frame(elevator_frame, bd=1, pady=10)
        status_box.pack(expand=True, fill=tk.X)
        status_text = tk.Label(status_box, text="Status:")
        status_text.pack(side=tk.LEFT)
        self.status = tk.Label(status_box, text="Still")
        self.status.pack(side=tk.LEFT)

    
    def _add_chat(self):
        """Adds widgets representing the chat window"""
        
        chat_frame = tk.Frame(self.root)
        
        # frame containing text box with messages and scrollbar
        self.text_frame = tk.Frame(chat_frame, bd=6)
        self.text_frame.pack(expand=True, fill=tk.BOTH)

        # scrollbar for text box
        self.text_box_scrollbar = tk.Scrollbar(self.text_frame, bd=0)
        self.text_box_scrollbar.pack(fill=tk.Y, side=tk.RIGHT)

        # contains messages
        self.text_box = tk.Text(self.text_frame, yscrollcommand=self.text_box_scrollbar.set, 
                                state=tk.DISABLED,bd=1, padx=6, pady=6, spacing3=8, wrap=tk.WORD, 
                                bg=None, relief=tk.GROOVE, width=10, height=1)
        self.text_box.pack(expand=True, fill=tk.BOTH)
        self.text_box_scrollbar.config(command=self.text_box.yview)

        # frame containing user entry field
        self.entry_frame = tk.Frame(chat_frame, bd=1)
        self.entry_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # entry field
        self.entry_field = tk.Entry(self.entry_frame, bd=1, justify=tk.LEFT)
        self.entry_field.focus_set()
        self.entry_field.pack(fill=tk.X, padx=6, pady=6, ipady=3)

        # frame containing send button and emoji button
        self.send_button_frame = tk.Frame(chat_frame, bd=0)
        self.send_button_frame.pack(fill=tk.BOTH)

        # send button
        self.send_button = tk.Button(self.send_button_frame, text="Send", width=5, relief=tk.GROOVE, 
                                     bg='white', bd=1, command=self._send_user_input)
        self.send_button.pack(side=tk.LEFT, padx=6, pady=8, ipady=3)
        self.root.bind("<Return>", self._send_user_input)
        
        chat_frame.pack(expand=True, fill=tk.BOTH)

        
    def _send_user_input(self, event=None):
        """Acts upon a submitted user input"""
        
        user_input = self.entry_field.get().strip("{").strip("}")
        self.entry_field.delete(0, tk.END)
        
        # we add some noise to the user input (to emulate ASR errors)
        noisy_input, confidence_score = self._add_noise(user_input)
             
        # create a new user turn and send it to the voice controller
        user_turn = DialogueTurn(speaker_name="Human", utterance=noisy_input, 
                                 confidence=confidence_score)        
        self.elevator.process_user_input(user_turn)
        
    
    def _add_noise(self, utterance, wer=0.07):
        """Simulate ASR errors by swapping letters in some words"""
        
        # We change a few letters in the utterance
        new_words = []
        for word in utterance.split():
            if len(word) > 2 and random.random() < wer:
                change_index = random.choice(range(1,len(word)-1))
                new_letter = random.choice(string.ascii_letters).lower()
                word = word[:change_index] + new_letter + word[change_index+1:]
            new_words.append(word)
        noisy_utterance = " ".join(new_words)
        
        # We sample the confidence score from a normal distribution
        confidence_score = np.random.normal(0.8, 0.1)
        if noisy_utterance != utterance:
            confidence_score -= np.random.normal(0.4,0.1)
        confidence_score = max(0, min(1, confidence_score))
        
        return noisy_utterance, confidence_score
        
        
    def display_turn(self, turn : DialogueTurn):
        """Shows a message in the chat window (with confidence score in parenthesis)"""

        self.text_box.configure(state=tk.NORMAL)
        conf_string = " (%.2f)"%turn.confidence if turn.confidence < 1 else ""
        self.text_box.insert(tk.END, "%s: %s%s\n"%(turn.speaker_name, turn.utterance, conf_string))
        self.text_box.see(tk.END)
        self.text_box.configure(state=tk.DISABLED)
        
        
    def trigger_movement(self):
        """Trigger a movement of the elevator if the list of next stops is not 
        empty. The movement continues until all goals are reached."""
        
        if self.elevator.next_stops:
            floor_to_reach = self.elevator.next_stops[0]
            
            if self.elevator.cur_floor == floor_to_reach:
                self.elevator.next_stops.pop(0)
                self.trigger_movement()
                return
            
            if floor_to_reach > self.elevator.cur_floor:
                next_floor = self.elevator.cur_floor+1
                self.status.config(text="UP")
            elif floor_to_reach < self.elevator.cur_floor:
                next_floor = self.elevator.cur_floor-1
                self.status.config(text="DOWN")
                   
            self.root.update()
            cur_floor_widget = self.floors[self.elevator.cur_floor]
            speed_ms = int(self.speed * 1000)
            cur_floor_widget.after(speed_ms, cur_floor_widget.config(bg="white"))
            self.elevator.cur_floor = next_floor
            cur_floor_widget = self.floors[self.elevator.cur_floor]
            cur_floor_widget.after(speed_ms, cur_floor_widget.config(bg="red"))
            self.trigger_movement()
            
        else:
            self.status.config(text="Still")
            self.root.update()
