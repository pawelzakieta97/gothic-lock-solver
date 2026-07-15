import numpy as np
class Lock:
    def __init__(self, positions: np.array, binds: np.array):
        self.positions = positions
        self.binds = binds
        self.limits = (0, 6)
        self.finishing_state = 3

    def copy(self):
        return Lock(self.positions.copy(), self.binds.copy())

    def move(self, index, amount, ignore_limits=False):
        positions = self.positions + self.binds[index, :] * amount
        if ignore_limits or np.all((positions >= self.limits[0]) & (positions <= self.limits[1])):
            self.positions = positions
        else:
            raise ValueError(f'Cant move from {self.positions.tolist()} to {positions.tolist()}')
        if np.all(self.positions == self.finishing_state):
            # print('Unlocked')
            return True
        return False

    def __hash__(self):
        return hash(str(self.positions.tolist()))

    def __eq__(self, other):
        return np.all(other.positions == self.positions) and np.all(other.binds == self.binds)

    def is_solved(self):
        return np.all(self.positions == self.finishing_state)

def get_possible_moves(lock: Lock):
    all_moves = np.array([[-1, 1]] * lock.positions.shape[0])
    indexes = np.arange(lock.positions.shape[0])
    resulting_positions = lock.positions[None, None, :] + lock.binds[indexes, None, :] * all_moves[:,:,None]
    valid = np.all((resulting_positions >= lock.limits[0]) & (resulting_positions <= lock.limits[1]), axis=-1)
    return [(int(index), int(all_moves[index, direction])) for index, direction in zip(*np.where(valid))]

def get_lock():
    return Lock(np.zeros(6), np.eye(6))

def get_random_lock(n=6, difficulty=0.5):
    positions = np.random.randint(0, 7, n)
    r = np.random.random((n,n))
    binds = np.zeros((n,n), dtype=int)
    binds[r < (difficulty/2)] = -1
    binds[r > (1-difficulty/2)] = 1
    binds[np.arange(n), np.arange(n)] = 1
    return Lock(positions, binds)

def solve(lock: Lock):
    try:
        if np.linalg.det(lock.binds.T) < 0.001:
            raise ValueError('Fucked matrix')
        target_moves = np.linalg.inv(lock.binds.T) @ (lock.finishing_state - lock.positions)
    except Exception as e:
        print(e)
        print('Attempting backup solver')
        return solve_backup(lock)
    if np.abs(np.round(target_moves) - target_moves).max() > 0.01:
        # return solve_backup(lock)
        raise ValueError('IMPOSSIBLE LOCK - FRACTIONS')
        return []
    explored = {}
    stack = {lock: ([], np.abs(target_moves).sum(), np.zeros(lock.positions.shape[0]))} # {lock: (current moves, remaining_estimate, total_inputs)}
    i = 0
    while True:
        if not stack:
            raise ValueError('IMPOSSIBLE LOCK - CHECKED ALL POSSIBLE MOVES')
            return []
        lock = min(stack.keys(), key=lambda key: len(stack[key][0]) + stack[key][1] * 1.01)
        performed_moves, current_estimate, total_inputs = stack[lock]
        if lock.is_solved():
            print(i)
            return performed_moves, explored, stack, i, 'linalg solver'

        del stack[lock]
        explored[lock] = (performed_moves, current_estimate, total_inputs)
        for possible_move in get_possible_moves(lock):
            i += 1
            new_lock = lock.copy()
            new_lock.move(*possible_move)
            if new_lock in explored:
                continue
            new_performed_moves = performed_moves + [possible_move]
            new_total_inputs = total_inputs.copy()
            new_total_inputs[possible_move[0]] += possible_move[1]
            remaining_estimate = np.abs(target_moves - new_total_inputs).sum()
            if new_lock in stack:
                if remaining_estimate != stack[new_lock][1]:
                    print('THIS SHOULD BE THE SAME')
                if len(new_performed_moves) >= len(stack[new_lock][0]):
                    continue
            stack[new_lock] = (new_performed_moves, remaining_estimate, new_total_inputs)


def solve_backup(lock: Lock):
    explored = {}
    stack = {lock: ([], np.abs(lock.positions-lock.finishing_state).sum())}  # {lock: (current moves, remaining_estimate)}
    i = 0
    while True:
        if not stack:
            raise ValueError('IMPOSSIBLE LOCK - CHECKED ALL POSSIBLE MOVES')
            return []
        lock = min(stack.keys(), key=lambda key: float(len(stack[key][0])) + float(stack[key][1]) * 1.01)
        performed_moves, current_estimate = stack[lock]
        if lock.is_solved():
            print(i)
            return performed_moves, explored, stack, i, 'backup solver'

        del stack[lock]
        explored[lock] = (performed_moves, current_estimate)
        for possible_move in get_possible_moves(lock):
            i += 1
            new_lock = lock.copy()
            new_lock.move(*possible_move)
            if new_lock in explored:
                continue
            new_performed_moves = performed_moves + [possible_move]
            remaining_estimate = np.abs(new_lock.positions-lock.finishing_state).sum()
            if new_lock in stack:
                if remaining_estimate != stack[new_lock][1]:
                    print('THIS SHOULD BE THE SAME')
                if len(new_performed_moves) >= len(stack[new_lock][0]):
                    continue
            stack[new_lock] = (new_performed_moves, remaining_estimate)

def parse_binds(binds: list[list[int]], n: int):
    b = np.eye(n, dtype=float)
    for y, bind in enumerate(binds):
        for bind_idx in bind:
            b[y, abs(bind_idx) - 1] = 1 if bind_idx > 0 else -1
    return b

def solve_lock(positions: list[int], binds: list[list[int]]):
    # E.G.  positions = [0,3,5,6,1,2]
    #       binds = [[2, -3], [-1], [6], [], [-2], [3]]
    b = parse_binds(binds, len(positions))
    lock = Lock(np.array(positions, dtype=float), b)
    try:
        moves, explored, stack, i, solver = solve(lock)
        # moves, explored, stack, i = solve_backup(lock)
        return f'Solved after considering {i} moves using {solver}\n' + '\n'.join([f'Component {idx+1} {"RIGHT" if direction < 0 else "LEFT"}' for idx, direction in moves])
    except Exception as e:
        return e
    return None